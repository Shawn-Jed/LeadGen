/* =====================================================================
   LeadGen — Frontend-Konfiguration
   ---------------------------------------------------------------------
   API_BASE bestimmt, gegen welches Backend das Frontend spricht.

   - Leerer String ("")  → gleiche Origin (Backend liefert das Frontend
     selbst aus: `python backend/app.py` ohne --api-only).
   - Absolute URL        → entkoppelter Betrieb: Frontend separat serviert
     (z.B. `npx serve frontend`), Backend läuft auf eigener Origin/Port.

   Für den Standard-Lokalbetrieb zeigt die Base auf das Backend auf 8723.
   Für ein Deployment hier die öffentliche API-URL eintragen.
   ===================================================================== */
window.LEADGEN_API_BASE = "http://127.0.0.1:8723";
