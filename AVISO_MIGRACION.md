# Este scraper ya no se usa

Desde octubre de 2026 los partidos del club los lee el gestor documental
(https://gestor-documental-cb.vercel.app) y la web pública es https://www.cbvalsequillo.com.

- `scraper_automatico.yml.desactivado`: el workflow antiguo en Python, apagado.
- `.github/workflows/partidos.yml`: el único workflow activo; cada 2 horas llama al gestor
  para que lea las hojas de jornada. Necesita el secret `GESTOR_CRON_SECRET` del repositorio.
- `docs/index.html`: aviso de mudanza con redirección a la web nueva.
