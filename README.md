# Dashboard de Gestión de Plazas

Dashboard interactivo para analizar plazas ocupadas, vacantes y reservadas a partir del Excel proporcionado.

## Archivos
- `app.py`: aplicación Streamlit.
- `requirements.txt`: dependencias.
- `REPORTE DE PLAZAS VACANTES, OCUPADAS Y RESERVADAS.XLSX`: fuente de datos.

## Ejecutar localmente
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Publicar en Streamlit Community Cloud
1. Sube los archivos a un repositorio de GitHub.
2. Entra en https://share.streamlit.io/
3. Selecciona el repositorio, la rama y `app.py`.
4. Pulsa Deploy.

## Privacidad
Antes de publicar el Excel en un repositorio público, confirma que tienes autorización para divulgar la información. Si el archivo contiene datos internos, usa un repositorio privado y revisa las políticas de tu organización.
