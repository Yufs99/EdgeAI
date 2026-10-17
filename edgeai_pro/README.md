# EDGEAI PRO 1.2

Streamlit-app med API-Football-baserad målstatistik och separat webbsökning efter odds hos flera spelbolag.

## Uppdatera GitHub
Ersätt `edgeai_pro/app.py` med den här filen. `requirements.txt` är oförändrad.

## Ny odds-funktion
Öppna `Hitta odds online – flera spelbolag` i appen. En valfri Brave Search API-nyckel kan anges i fältet eller i Streamlit Secrets som `BRAVE_SEARCH_API_KEY`. Sökresultat är länkar och textutdrag, **inte verifierade liveodds**. Utan söknyckel får du en Google-söklänk. Kontrollera odds själv och använd `Kontrollera odds och jämför med minimiodds`.

## API-nycklar
Lägg aldrig API-nycklar i GitHub. API-Football kan anges som `API_FOOTBALL_KEY` i Streamlit Secrets.

## Begränsningar
Denna version ger inte fullständig marknadstäckning. Den befintliga analysmodellen analyserar endast målmarknader och båda lagen gör mål. Gratis API-Football kan blockera `last`-parametern och nya säsonger. Historiken lagras i lokal SQLite på Streamlit-servern och kan försvinna vid omstart/omdistribution. Modellens sannolikheter är okalibrerade. Sökresultat från webben ska inte automatiskt tolkas som tillgängliga priser.
