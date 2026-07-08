"""
GENERADOR DE LICENCIAS DRXOPTI — PRIVADO, NUNCA LO DISTRIBUYAS
================================================================
Uso:
  1. Primera vez:      python tools/keygen.py --init
     (crea tu par de llaves; la privada queda en tools/private_key.pem — GUÁRDALA)
  2. Generar clave:    python tools/keygen.py --cliente "nombre o email"
  3. Generar varias:   python tools/keygen.py --cliente "juan" --cantidad 5

Cada clave incluye el nombre del cliente firmado — si alguien filtra su clave
puedes saber exactamente quién fue.
"""
import argparse
import base64
import os
import sys
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

TOOLS_DIR   = os.path.dirname(os.path.abspath(__file__))
PRIVATE_PEM = os.path.join(TOOLS_DIR, "private_key.pem")
PUBLIC_PY   = os.path.join(TOOLS_DIR, "..", "core", "public_key.py")
LOG_FILE    = os.path.join(TOOLS_DIR, "claves_generadas.txt")


def init_keys():
    if os.path.exists(PRIVATE_PEM):
        print("[!] Ya existe private_key.pem — si la regeneras, TODAS las claves")
        print("  vendidas dejarán de funcionar. Aborta si no es lo que quieres.")
        if input("  Escribe SI para continuar: ").strip() != "SI":
            return

    private_key = Ed25519PrivateKey.generate()

    with open(PRIVATE_PEM, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    pub_b64 = base64.b64encode(pub_bytes).decode()

    with open(PUBLIC_PY, "w", encoding="ascii") as f:
        f.write('# Llave publica de verificacion - se distribuye con la app\n')
        f.write(f'PUBLIC_KEY_B64 = "{pub_b64}"\n')

    print("OK Llaves generadas:")
    print(f"  PRIVADA (secreta):  {PRIVATE_PEM}")
    print(f"  PÚBLICA (en app):   {os.path.abspath(PUBLIC_PY)}")
    print("\n[!] RESPALDA private_key.pem en un lugar seguro (USB, nube privada).")
    print("  Si la pierdes no podrás generar más claves compatibles.")


def generate_key(cliente: str) -> str:
    with open(PRIVATE_PEM, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Payload: cliente|timestamp
    payload = f"{cliente}|{int(time.time())}"
    payload_b = payload.encode()

    signature = private_key.sign(payload_b)

    # Clave = base64(payload) . base64(firma)
    key = (
        base64.urlsafe_b64encode(payload_b).decode().rstrip("=")
        + "."
        + base64.urlsafe_b64encode(signature).decode().rstrip("=")
    )
    return f"DRXO-{key}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--init", action="store_true", help="Genera el par de llaves inicial")
    p.add_argument("--cliente", type=str, help="Nombre o email del comprador")
    p.add_argument("--cantidad", type=int, default=1)
    args = p.parse_args()

    if args.init:
        init_keys()
        return

    if not args.cliente:
        p.print_help()
        return

    if not os.path.exists(PRIVATE_PEM):
        print("X No existe private_key.pem — corre primero: python tools/keygen.py --init")
        sys.exit(1)

    print(f"\nClaves para: {args.cliente}\n" + "-" * 60)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        for i in range(args.cantidad):
            key = generate_key(args.cliente)
            print(key)
            log.write(f"{time.strftime('%Y-%m-%d %H:%M')} | {args.cliente} | {key}\n")
    print("-" * 60)
    print(f"OK Registradas en {LOG_FILE}")


if __name__ == "__main__":
    main()

