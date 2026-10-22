# CareCompass – Friction log (Amazon Developer Hackathon)

1. **Task:** LLM → `screen_care_barriers`. **Expected:** correct flags. **Actual:** the LLM invented answer keys and got a silent "low" tier. **Severity:** high (a safety-relevant false negative). **Workaround:** strict schema + `unknown_answer_keys`. **Suggestion:** have Alexa+ validate tool arguments against the inputSchema and surface the errors to the developer.
2. **Task:** test against real Alexa+. **Actual:** no sandbox or simulator for a self-hosted MCP. **Severity:** medium. **Workaround:** `alexa_sim.py`. **Suggestion:** publish an Alexa+ MCP test console.
3. **Task:** the model filled in an `oop_remaining` of 5000 that the user never said. **Severity:** low here (the result doesn't change), but it is a risk. **Suggestion:** guidance on when Alexa+ should ask a follow-up question versus defaulting an argument.
