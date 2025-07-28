from solana.rpc.api import Client
from solders.pubkey import Pubkey

client = Client("https://api.mainnet-beta.solana.com")

def verify_payment(reference_key: str, expected_amount: float = None, token_mint: str = None):
    """Verify SPL token payment using reference key"""
    reference_pubkey = Pubkey.from_string(reference_key)

    sigs = client.get_signatures_for_address(reference_pubkey, limit=10)
    if not sigs.value:
        return False, "No transactions found"

    for sig_info in sigs.value:
        tx = client.get_transaction(sig_info.signature, encoding="jsonParsed")
        if not tx.value:
            continue

        instructions = tx.value.transaction.transaction.message.instructions
        for instruction in instructions:
            if hasattr(instruction, 'parsed') and instruction.parsed:
                parsed = instruction.parsed
                if parsed.get('type') == 'transferChecked' and 'info' in parsed:
                    info = parsed['info']

                    # Verify amount if specified
                    if expected_amount:
                        amount = float(info.get('tokenAmount', 0).get(
                            "amount")) / 1e9  # Assuming 9 decimals
                        if amount != expected_amount:
                            continue

                    # Verify token mint if specified
                    if token_mint and info.get('mint') != token_mint:
                        continue

                    return True, str(sig_info.signature)

    return False, "Payment not verified"
