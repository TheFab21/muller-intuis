#!/usr/bin/env python3
"""Script de test pour valider l'authentification Muller Intuitiv."""

import asyncio
import json
import sys
from datetime import datetime

import aiohttp


async def test_auth(client_id: str, client_secret: str, username: str, password: str):
    """Test l'authentification avec l'API Muller Intuitiv."""
    
    print("=" * 60)
    print("TEST D'AUTHENTIFICATION MULLER INTUITIV")
    print("=" * 60)
    print()
    
    # Paramètres d'authentification
    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
        "grant_type": "password",
        "user_prefix": "muller",
        "scope": "read_muller write_muller",
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    url = "https://app.muller-intuitiv.net/oauth2/token"
    
    print(f"📡 Tentative de connexion à : {url}")
    print(f"👤 Username: {username}")
    print()
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🔄 Envoi de la requête d'authentification...")
            async with session.post(url, data=auth_data, headers=headers) as response:
                status = response.status
                
                print(f"📊 Status HTTP: {status}")
                print()
                
                if status == 200:
                    data = await response.json()
                    
                    print("✅ AUTHENTIFICATION RÉUSSIE !")
                    print()
                    print("📋 Informations de token:")
                    print(f"   • Access Token: {data['access_token'][:20]}...{data['access_token'][-20:]}")
                    print(f"   • Refresh Token: {data['refresh_token'][:20]}...{data['refresh_token'][-20:]}")
                    print(f"   • Expires in: {data['expires_in']} secondes ({data['expires_in'] / 3600:.1f} heures)")
                    print(f"   • Token type: {data.get('token_type', 'Bearer')}")
                    
                    # Calculer l'heure d'expiration
                    expiry_time = datetime.now().timestamp() + data['expires_in']
                    expiry_datetime = datetime.fromtimestamp(expiry_time)
                    print(f"   • Expiration: {expiry_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
                    
                    # Afficher le JSON complet (masqué)
                    print("📄 Réponse JSON complète (tokens masqués):")
                    safe_data = data.copy()
                    if 'access_token' in safe_data:
                        safe_data['access_token'] = safe_data['access_token'][:20] + "..." + safe_data['access_token'][-20:]
                    if 'refresh_token' in safe_data:
                        safe_data['refresh_token'] = safe_data['refresh_token'][:20] + "..." + safe_data['refresh_token'][-20:]
                    print(json.dumps(safe_data, indent=2))
                    print()
                    
                    return True
                else:
                    error_text = await response.text()
                    print("❌ ÉCHEC DE L'AUTHENTIFICATION")
                    print()
                    print(f"Erreur HTTP {status}:")
                    print(error_text)
                    print()
                    
                    if status == 400:
                        print("💡 Conseils:")
                        print("   • Vérifiez que le Client ID et Client Secret sont corrects")
                        print("   • Vérifiez que le username (email) et password sont corrects")
                        print("   • Assurez-vous d'utiliser les identifiants de l'app Muller Intuitiv")
                    elif status == 401:
                        print("💡 Conseils:")
                        print("   • Vérifiez votre username (email) et password")
                        print("   • Testez d'abord dans l'application mobile Muller Intuitiv")
                    
                    return False
                    
        except aiohttp.ClientError as err:
            print(f"❌ ERREUR DE CONNEXION: {err}")
            print()
            print("💡 Conseils:")
            print("   • Vérifiez votre connexion internet")
            print("   • Vérifiez que l'URL de l'API est accessible")
            return False
        except Exception as err:
            print(f"❌ ERREUR INATTENDUE: {err}")
            return False


async def main():
    """Fonction principale."""
    print()
    print("🔧 Configuration")
    print("-" * 60)
    
    # Demander les identifiants
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    username = input("Username (email): ").strip()
    password = input("Password: ").strip()
    
    print()
    
    if not all([client_id, client_secret, username, password]):
        print("❌ Erreur: Tous les champs sont obligatoires")
        return 1
    
    success = await test_auth(client_id, client_secret, username, password)
    
    print("=" * 60)
    if success:
        print("✅ Test réussi ! Vous pouvez utiliser ces identifiants dans Home Assistant.")
    else:
        print("❌ Test échoué. Vérifiez vos identifiants et réessayez.")
    print("=" * 60)
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        sys.exit(1)
