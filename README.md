# capital-mapa-pro

API en Node.js + Express con esquema SQL para Supabase, enfocada en capitales, países y puntos de interés.

## Requisitos

- Node.js 18+
- Supabase/PostgreSQL

## Configuración

1. Crea una base de datos en Supabase.
2. Ejecuta el SQL en `supabase/schema.sql`.
3. Crea un archivo `.env` con la variable:

```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

## Uso

```bash
npm install
npm run dev
```

La API estará disponible en `http://localhost:3000/api`.

### Endpoints

- `GET /api/health`
- `GET /api/countries`
- `GET /api/capitals`
- `GET /api/capitals/:id`
- `GET /api/landmarks`
