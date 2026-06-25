# 🗺️ Mapa Interactivo Yacu Warmi

Mapa interactivo del **Corredor de Conectividad Comunitaria** de la provincia de
Napo, Ecuador. Publicado como sitio estático en GitHub Pages.

🌐 **[Ver el mapa en vivo](https://TU-USUARIO.github.io/TU-REPOSITORIO/)**

## Estructura del proyecto

```
├── docs/                  ← Sitio estático (GitHub Pages)
│   ├── index.html         ← Mapa interactivo
│   ├── assets/
│   │   ├── images/        ← Fotos iNaturalist + logos
│   │   └── vendor/        ← Leaflet, Proj4 (offline)
│   ├── inset_ecuador.png
│   └── inset_napo.png
│
├── src/yacuwarmi_map/     ← Paquete Python (CLI de construcción)
├── data/                  ← Datos geoespaciales (GeoJSON, JSON)
├── tools/                 ← Scripts de utilidad y extracción
├── assets/                ← Assets fuente (imágenes originales)
└── tests/                 ← Tests
```

## Publicación en GitHub Pages

El sitio se sirve directamente desde la carpeta `docs/` en la rama `main`.

### Configuración inicial en GitHub

1. Crear un repositorio en GitHub
2. Vincular el repositorio local:

```bash
git remote add origin https://github.com/TU-USUARIO/TU-REPOSITORIO.git
git push -u origin main
```

3. En GitHub → **Settings** → **Pages**:
   - Source: **GitHub Actions**
   - El workflow `.github/workflows/deploy.yml` se encarga del deploy automático

### Deploy manual (alternativa)

Si prefieres no usar Actions, configura Pages desde:
- Source: **Deploy from a branch**
- Branch: `main` / carpeta: `/docs`

## Desarrollo local

### Requisitos

- Python 3.11 o superior
- `uv` recomendado, o `pip` como alternativa
- Google Chrome/Chromium (solo para exportar PDF)

### Instalación con uv

```bash
uv sync --extra pdf --extra dev --frozen
uv run mapa all
uv run pytest
```

### Instalación con pip

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[pdf,dev]"
mapa all
pytest
```

### Comandos disponibles

| Comando | Descripción |
|---|---|
| `mapa build` | Genera el HTML en `docs/` |
| `mapa validate` | Valida datos y recursos |
| `mapa all` | Construye y valida |
| `mapa export-pdf --dpi 600` | Exporta PDF A0 vectorial |

### Exportación PDF

```bash
uv run mapa export-pdf --dpi 600
```

La exportación genera un PDF A0 horizontal con texto y geometrías vectoriales.
Requiere Chrome/Chromium y el extra `pdf` (Pillow + Playwright).

## Datos

Los JSON y GeoJSON en `data/` constituyen el snapshot procesado utilizado por
la construcción. Los datos de iNaturalist no se actualizan automáticamente.

Los scripts en `tools/` son utilidades históricas de extracción y depuración
que requieren los archivos fuente QGIS/GeoPackage originales.

## Tecnologías

- [Leaflet](https://leafletjs.com/) — Mapas interactivos
- [Proj4js](http://proj4js.org/) — Transformación de coordenadas
- [iNaturalist](https://www.inaturalist.org/) — Datos de biodiversidad
