# EDGEAI PRO 1.0 – första fungerande prototyp

En Streamlit-app med API-Football, strikt tävlingsfilter, målmarknadsscreening, tydligt markerade modellskattningar, minimiodds och SQLite-historik.

## Kör lokalt

```bash
pip install -r requirements.txt
streamlit run app.py
```

Öppna webbadressen som visas och ange din API-Football-nyckel i sidomenyn. Nyckeln sparas inte i historiken. Alternativt: lägg `API_FOOTBALL_KEY = "..."` i Streamlits secrets.

## Publicera gratis

1. Skapa ett privat GitHub-repository och ladda upp `app.py` och `requirements.txt`.
2. Gå till https://share.streamlit.io och välj **Create app** från GitHub-repot.
3. Ange `app.py` som startfil och publicera.
4. Lägg API-nyckeln i Streamlit-appens Secrets om du inte vill ange den vid varje körning.

**Viktigt:** Gratis Streamlit Community Cloud har inte garanterad permanent lokal disklagring. SQLite-historiken kan försvinna vid omstart/ompublicering. För varaktig historik behövs extern databas, exempelvis Supabase. På delad app bör nyckeln inte exponeras för andra användare.

## Begränsningar – ärligt redovisade

- **Endast målmarknader och båda lagen gör mål är implementerade.** Inte 1X2, hörnor, kort, skott eller spelarmarknader.
- **Inget odds-API är anslutet.** Alla förslag är kandidater, inte bekräftade spelvärden.
- Modellen använder gjorda och insläppta mål från upp till 10 tidigare matcher per lag, förenklad Poissonfördelning och en försiktig justering mot 50 %. Det är en heuristik, **inte en validerad eller kalibrerad sannolikhetsmodell**.
- Styrkebetyget är en sorteringsheuristik, inte en objektiv kvalitetsgaranti.
- API-Football gratisplan kan sakna relevanta säsonger och snabbt slå i anropsgränsen.
- Matcher som startat eller avslutats exkluderas.
- SQLite-historiken sparas lokalt på den server som kör appen.

## Nästa steg

Anslut odds-API; implementera marknadsspecifika modeller för hörnor, kort, spelarskott och 1X2; backtesta och kalibrera sannolikheterna; lagra historik i extern databas. Gör först därefter verklig ranking efter uppskattat spelvärde.
