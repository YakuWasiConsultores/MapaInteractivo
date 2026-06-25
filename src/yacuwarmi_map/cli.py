from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


HTML_NAME = "index.html"
DATA_DIR = "data"
TOOLS_DIR = "tools"
DATA_FILES = (
    "communities_geo.json",
    "corridor_polygon.json",
    "inaturalist_data.json",
    "KBA.geojson",
    "SNAP.geojson",
    "Posibles_comunidades.geojson",
    "Ecu_25.geojson",
    "Corredor_NorOriental.geojson",
    "Napo.geojson",
)


class ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.local: list[str] = []
        self.remote: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key not in {"src", "href"} or not value or value.startswith("#"):
                continue
            if value.startswith(("http://", "https://")):
                self.remote.append(value)
            else:
                self.local.append(value)


def project_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if (cwd / TOOLS_DIR / "generate_html.py").exists():
        return cwd
    return Path(__file__).resolve().parents[2]


def copy_runtime_assets(root: Path, dist: Path) -> None:
    for name in ("inset_ecuador.png", "inset_napo.png"):
        shutil.copy2(root / name, dist / name)
    shutil.copytree(root / "assets", dist / "assets", dirs_exist_ok=True)


def build(root: Path, dist: Path) -> Path:
    dist.mkdir(parents=True, exist_ok=True)
    copy_runtime_assets(root, dist)
    output = dist / HTML_NAME
    subprocess.run(
        [
            sys.executable,
            str(root / TOOLS_DIR / "generate_html.py"),
            "--project-root",
            str(root),
            "--output",
            str(output),
        ],
        check=True,
    )
    print(f"Paquete generado en {dist}")
    return output


def validate(root: Path, dist: Path) -> list[str]:
    errors: list[str] = []
    for name in DATA_FILES:
        path = root / DATA_DIR / name
        if not path.exists():
            errors.append(f"Falta el archivo de datos: {name}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"JSON inválido en {name}: {exc}")

    communities_path = root / DATA_DIR / "communities_geo.json"
    inat_path = root / DATA_DIR / "inaturalist_data.json"
    if communities_path.exists() and inat_path.exists():
        communities = json.loads(communities_path.read_text(encoding="utf-8"))
        inat = json.loads(inat_path.read_text(encoding="utf-8"))
        ids = [str(item["id"]) for item in communities]
        if len(communities) != 25:
            errors.append(f"Se esperaban 25 comunidades y se encontraron {len(communities)}")
        if len(ids) != len(set(ids)):
            errors.append("Los IDs de comunidades no son únicos")
        missing_species = sorted(set(ids) - set(inat.get("community_species", {})), key=int)
        if missing_species:
            errors.append(f"Faltan datos iNaturalist para IDs: {', '.join(missing_species)}")
        photo_references: set[str] = set()
        for community in inat.get("community_species", {}).values():
            for list_name in ("all_species", "fauna_species", "flora_species"):
                for species in community.get(list_name, []):
                    photo = species.get("photo_url", "")
                    if photo and not photo.startswith(("http://", "https://")):
                        photo_references.add(photo)
        for reference in sorted(photo_references):
            if not (root / reference).exists():
                errors.append(f"Foto iNaturalist inexistente: {reference}")

    html_path = dist / HTML_NAME
    if not html_path.exists():
        errors.append(f"No existe la salida construida: {html_path}")
        return errors

    html = html_path.read_text(encoding="utf-8")
    parser = ResourceParser()
    parser.feed(html)
    if parser.remote:
        errors.append("El HTML todavía depende de recursos remotos")
    for reference in sorted(set(parser.local)):
        if not (dist / reference).exists():
            errors.append(f"Recurso local inexistente: {reference}")
    if "var corredorNorData" not in html:
        errors.append("La capa Corredor NorOriental no fue incorporada")
    if "switchEditorCommunity()" in html or "updateImg()" in html:
        errors.append("El HTML contiene controles del editor sin implementación")
    return errors


def find_ghostscript() -> str | None:
    for executable in ("gs", "gswin64c", "gswin32c"):
        path = shutil.which(executable)
        if path:
            return path
    return None


def optimize_pdf_for_print(source: Path, output: Path, dpi: int) -> bool:
    ghostscript = find_ghostscript()
    if not ghostscript:
        shutil.copy2(source, output)
        return False

    subprocess.run(
        [
            ghostscript,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.7",
            "-dPDFSETTINGS=/prepress",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dDetectDuplicateImages=true",
            "-dCompressFonts=true",
            "-dSubsetFonts=true",
            "-dPassThroughJPEGImages=true",
            "-dDownsampleColorImages=false",
            "-dDownsampleGrayImages=false",
            "-dDownsampleMonoImages=false",
            f"-dColorImageResolution={dpi}",
            f"-dGrayImageResolution={dpi}",
            f"-dMonoImageResolution={max(dpi, 1200)}",
            f"-sOutputFile={output}",
            str(source),
        ],
        check=True,
    )
    return True


def collect_raster_quality(page, requested_dpi: int) -> dict[str, object]:
    images = page.locator("img").evaluate_all(
        """
        images => images.map((image, index) => {
          const rect = image.getBoundingClientRect();
          return {
            index,
            source: image.getAttribute("src") || "",
            natural_width: image.naturalWidth,
            natural_height: image.naturalHeight,
            rendered_width_css_px: Number(rect.width.toFixed(2)),
            rendered_height_css_px: Number(rect.height.toFixed(2)),
            effective_dpi_x: rect.width
              ? Number((image.naturalWidth / rect.width * 96).toFixed(1))
              : null,
            effective_dpi_y: rect.height
              ? Number((image.naturalHeight / rect.height * 96).toFixed(1))
              : null
          };
        })
        """
    )
    below_target = [
        image
        for image in images
        if min(
            image.get("effective_dpi_x") or requested_dpi,
            image.get("effective_dpi_y") or requested_dpi,
        )
        < requested_dpi
    ]
    return {
        "requested_dpi": requested_dpi,
        "page_format": "A0 landscape",
        "vector_content": True,
        "note": (
            "Texto, geometrías y líneas permanecen vectoriales. El DPI efectivo "
            "solo limita fotografías y otras imágenes raster."
        ),
        "raster_images": images,
        "raster_images_below_requested_dpi": len(below_target),
    }


def prepare_print_rasters(page, html_dir: Path, dpi: int) -> list[dict[str, object]]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit(
            "Falta Pillow para preparar imágenes a resolución de impresión. "
            "Instala `.[pdf]` o ejecuta `uv sync --extra pdf`."
        ) from exc

    measurements = collect_raster_quality(page, dpi)["raster_images"]
    requirements: dict[str, tuple[int, int]] = {}
    for image in measurements:
        source = image["source"]
        if not source or source.startswith(("http://", "https://", "data:")):
            continue
        required_width = math.ceil(image["rendered_width_css_px"] * dpi / 96)
        required_height = math.ceil(image["rendered_height_css_px"] * dpi / 96)
        current_width, current_height = requirements.get(source, (0, 0))
        requirements[source] = (
            max(current_width, required_width),
            max(current_height, required_height),
        )

    print_dir = html_dir / "assets" / "print"
    if print_dir.exists():
        shutil.rmtree(print_dir)
    print_dir.mkdir(parents=True, exist_ok=True)
    replacements: dict[str, str] = {}
    upscaled: list[dict[str, object]] = []
    for source, (required_width, required_height) in requirements.items():
        source_path = html_dir / source
        if not source_path.exists():
            continue
        with Image.open(source_path) as image:
            scale = max(required_width / image.width, required_height / image.height, 1)
            if scale <= 1:
                continue
            target_size = (
                math.ceil(image.width * scale),
                math.ceil(image.height * scale),
            )
            resized = image.resize(target_size, Image.Resampling.LANCZOS)
            has_alpha = "A" in resized.getbands()
            output_suffix = ".png" if has_alpha else ".jpg"
            output_name = f"{Path(source).stem}@{dpi}dpi{output_suffix}"
            output_path = print_dir / output_name
            if has_alpha:
                resized.save(output_path, format="PNG", compress_level=1)
            else:
                resized.convert("RGB").save(
                    output_path,
                    format="JPEG",
                    quality=95,
                    subsampling=0,
                    optimize=False,
                )
            relative_output = output_path.relative_to(html_dir).as_posix()
            replacements[source] = relative_output
            upscaled.append(
                {
                    "source": source,
                    "print_source": relative_output,
                    "original_size": [image.width, image.height],
                    "print_size": list(target_size),
                    "interpolation": "Lanczos",
                }
            )

    if replacements:
        page.evaluate(
            """
            replacements => Promise.all(
              Array.from(document.images).map(image => {
                const source = image.getAttribute("src") || "";
                if (!replacements[source]) return Promise.resolve();
                image.src = replacements[source];
                return image.decode ? image.decode().catch(() => {}) : Promise.resolve();
              })
            )
            """,
            replacements,
        )
    return upscaled


def export_pdf(html: Path, output: Path, dpi: int, upscale_rasters: bool = True) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Falta Playwright. Instala las dependencias PDF con "
            "`python -m pip install -e .[pdf]` o `uv sync --extra pdf`."
        ) from exc

    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    output.parent.mkdir(parents=True, exist_ok=True)
    device_scale_factor = max(1.0, dpi / 96)
    with tempfile.TemporaryDirectory(prefix="yacuwarmi-pdf-") as temp_dir:
        raw_pdf = Path(temp_dir) / "raw.pdf"
        with sync_playwright() as playwright:
            launch_args: dict[str, object] = {"headless": True}
            if chrome:
                launch_args["executable_path"] = chrome
            browser = playwright.chromium.launch(**launch_args)
            page = browser.new_page(device_scale_factor=device_scale_factor)
            page.goto(html.resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            original_quality = collect_raster_quality(page, dpi)
            upscaled = prepare_print_rasters(page, html.parent, dpi) if upscale_rasters else []
            quality = collect_raster_quality(page, dpi)
            quality["device_scale_factor"] = device_scale_factor
            quality["original_raster_images_below_requested_dpi"] = original_quality[
                "raster_images_below_requested_dpi"
            ]
            quality["interpolated_raster_images"] = upscaled
            quality["interpolation_note"] = (
                "Las copias Lanczos alcanzan la densidad de píxeles solicitada, "
                "pero la interpolación no crea detalle fotográfico nuevo."
            )
            page.pdf(
                path=str(raw_pdf),
                format="A0",
                landscape=True,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                prefer_css_page_size=True,
            )
            browser.close()

        quality["ghostscript_prepress"] = optimize_pdf_for_print(raw_pdf, output, dpi)
        quality_path = output.with_suffix(".quality.json")
        quality_path.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    below_target = quality["raster_images_below_requested_dpi"]
    print(f"PDF A0 vectorial generado con objetivo de {dpi} DPI: {output}")
    print(f"Informe de calidad: {quality_path}")
    if below_target:
        print(
            f"ADVERTENCIA: {below_target} imágenes raster no alcanzan {dpi} DPI "
            "por la resolución de sus archivos fuente.",
            file=sys.stderr,
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="mapa", description="Construcción reproducible del mapa Yacu Warmi.")
    parser.add_argument("--project-root", help="Directorio raíz del proyecto.")
    parser.add_argument("--dist", default="docs", help="Directorio de salida relativo a la raíz.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="Genera el paquete HTML offline.")
    subparsers.add_parser("validate", help="Valida datos y recursos generados.")
    pdf_parser = subparsers.add_parser("export-pdf", help="Genera un PDF A0 de una página.")
    pdf_parser.add_argument("--output", default="mapa_corredor_biodiversidad.pdf")
    pdf_parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="DPI objetivo para efectos rasterizados y control de calidad (predeterminado: 600).",
    )
    pdf_parser.add_argument(
        "--no-raster-upscale",
        action="store_true",
        help="No crea copias interpoladas para imágenes fuente inferiores al DPI solicitado.",
    )
    subparsers.add_parser("all", help="Construye y valida el paquete.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = project_root(args.project_root)
    dist = (root / args.dist).resolve()

    if args.command in {"build", "all"}:
        build(root, dist)

    if args.command in {"validate", "all"}:
        errors = validate(root, dist)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("Validación completada sin errores.")

    if args.command == "export-pdf":
        if args.dpi < 300:
            raise SystemExit("El DPI de exportación debe ser al menos 300.")
        html = dist / HTML_NAME
        if not html.exists():
            html = build(root, dist)
        export_pdf(html, dist / args.output, args.dpi, not args.no_raster_upscale)
    return 0
