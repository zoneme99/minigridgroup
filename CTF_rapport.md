# Capture The Flag With Multi Agents

Vi har skapat ett environment där vi kan träna agenter som både har roller som defender och attacker.
Banorna är slumpade varje gång och alla i vår grupp har samma förutsättningar men har möjlighet att konfigurera egna rewards på olika beteenden.

### Exempel på en match


![CTF Match](self_play_match.gif)

## Mitt Bidrag

Jag fick vara med att lägga till en wrapper för all reward policy. Den finns under reward_logic.py. Detta var för att enkelt se och få en dashboard för all rewards man kunde tweaka.
