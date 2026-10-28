"""WhatsApp web kholne ke CDP constants (config_tools.py se 28-Oct aaye).

5-Oct: ye char constant `config_wake.py` me theek se nahi thhe (file 200 cross
kar gayi thi) — aur wake se inka koi lena-dena nahi. WhatsApp Web ek **tool**
hai, is liye ghar yahi hai. `config.py` inhe re-export karta hai,
is liye `config.CDP_PORT` jaisa references badalte nahi hue chalega.

Edge/Chrome is port par remote debug mode me chalta hai; pehli baar QR scan.
"""

WHATSAPP_WEB = "https://web.whatsapp.com"
CDP_PORT = 9222
CDP_HOST = "127.0.0.1"
CALL_ASK_FIRST = True         # call se pehle confirm card (gatekeeper ka ASK)
