#!/usr/bin/env bash
#
# Swiss AI Hub - Published Secret Check
#
# Refuses an env file that still holds a secret placeholder setup-env.sh fills, or a secret
# the repository has published. Until setup-env.sh generated them, .env.dev shipped fixed
# secrets, and an .env copied from it (or from a developer's .env) carries them to a server.
# Each is public on GitHub, so anyone can use it against that deployment.
#
# The values are kept as SHA-256 of "NAME=value", so the check matches the variable as well as
# the value and the script holds no secret in plain text.
#
# Usage:
#     ./check-env-secrets.sh            # checks .env
#     ./check-env-secrets.sh path/.env

set -euo pipefail

ENV_FILE="${1:-.env}"

command -v openssl >/dev/null 2>&1 || {
    echo "ERROR: 'openssl' is required but not found." >&2
    exit 1
}

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: Env file not found: $ENV_FILE" >&2
    exit 1
fi

# Every secret value .env.dev ever carried, as sha256("NAME=value").
PUBLISHED_SHA256="
04ead59ed555d7b4b4cb3422f757086d0fa5328e4d7b156aa2c594913dab7f51
15f59a2bf8a705fc542d701da470865d4247296ef5a7b7260d291807f1e7263a
17b55f68a4c9196ea91a14e9462d99e49280ae4c2be76be5fa6d7255168d0ffa
1e431e69076759f0fb9502c5117606af011424dd29d361aa92399c49f2e61311
23418b97cd7d539b3462d9fe16accad040c385057fc755e96c706bb9e6fabb6d
29a4d2abd68606456abce7fae3b652db800c7cfe5c48024fa94c22cd2dd398fc
29a9e427b312f6257aa3a500460185747a31abf4cb41c3cfe36a27f5bc52fbe5
2a213e3a7421b817a49926a094c1c3c0f281eb06153f46ecbac3bef43192fd94
2ff431907a84499136a7be86dbef10065dfd7e5389ac1ebc291c95e8d4856030
3348a7b504031211358976a56e6e8aac1709c75a125c9477dafc99b0f55fbf5e
3ad3e8cdfd3c0cd5dff2d69245a3a9d08b50039cb747dfcb07cee4cfd1b2cbc9
43bd546c03903a67c6f34793ed51ccc49205637b03d96734ee54d2db6a24df1e
4731a0f8957261cadfc2e12968caca4782f86d8ff68bf92f0347715717cd99d2
47b45213769a4c87869e25d044204d8a81419cf7ea6b5c0d52ee0fe27e8efd81
5cd267adfd9b5986a0cd8c311b1dfafded868bac6429b26787c5358b8941c8ac
6266b9d2ea13029f9c84352b22bdf94fc77d496912632510515564532c574fcf
67686043eb9080b2faeb533d0782b07024fceebd01a304b0907d9d4b6f920142
69d435195af7d5bf6561fb0490e56cf63fe3fd896c3693cc3416b91cd7cd814b
6af267d0558b24245211c793654594058597bf25a19e6f1e51bd779120a18e3c
73163eebc1af99f129eed79d2d91746d8250b0df2a71b4a6a40ea6c8d8a8da83
7e6a3668b5bf23c32507d39466cb47dd8672a95466838f02b950a6c58c7741d0
87cb6b2f5cf8a1e65eeeeca78e0c1e9c12e3d6834d8d4edc9eb9235049c8c7af
92e37d32d8839354f4abdba8b6fa890f58fdea04aea2f7050d71e5df56a84f1b
947c94868b5ba20d4da6725bc06b06b2cb9931c70c327a2549208a130c43828d
94d817877d0570a6fa4f06fcc5d55db93c750b2c375a59c523c12e06e8fe7050
9d373c981dcf816351981d641a24ecad755f40930b65698b975290585de3767a
9fee53ee8b7ec25138455357d2ac6e6690a9bfe62f462cb390e80bafe841f0fd
a2203b792c2e5dd3743aa9844fcef08927a6547cf964916d015c9865f983782e
a3a7032a3deb53b47f977926ad7012a206267100bc4ef03365f6639560a7f5cb
a3f0649191efa894fc17020a57da8842a0d279023ea17dcaa27bc9e51c8c01b7
b6e252d8c9ad6632546942e425600a5ce0220c8556ef0fcfa874c690b880f572
b9480630f7f43dfee59cc4a82a86d1dcdf6daefb8eaf08db45b18a2ee58e82b9
c2cedc704c69d1919461a49d017b660a1ac3b97a6a2ce58f969725245270fbf7
c51e7cf3f62825dae0c26e0055769d90828d09354506ca30de18c7c58270a1bb
c58b00aa286265d65a016af894c5acfbd10dd5af733f00e3a0a53157599aa682
c9024906d14b8f5bb4c17947ec439a62b14ed250702fff97fa1af046db9f4c2d
cd3e4484228e971329259f21a75c0f562abcafb99e878c2f8957d7e219b5f403
d04eba6117681c4b3a8ce8d4e582bcc4c6da094faf458b8ec1d240069c7156b8
d477c72820583dcef17cfb9af5dfb96eec4defb8bbc852b6f4d22dacca746ec4
db3f2794645519be99648fd65de1e6d34a840aa4c46645e4cbb45619bd159916
e9b688fa539c51d7b68f4ed4d98ca1fdbfb075ed35223f057bedd6aedd60663f
f523c838e619bdb94d09f06de3a6f34a02d24f8e0b0b08819c8f23cbacd05f9c
f58a7eb77ccc758893cc452ee9faf304b44243f5b2fe597e513bb206a0b55546
f796bc87cb36e4403d1613b796113665e9d4ac5890e20b6291f3e7c1016bdddf
fd72a9f1c4ddd9e5c6c77ff5879d2e4c006d8d1fee23d675445d5f09d5fc03dd
"

GENERATED_PLACEHOLDER='REPLACE_WITH_(RANDOM_STRING|64_HEX_CHARS|RANDOM_UUID|FERNET_KEY|LANGFUSE_)'

failures=0
while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || continue
    name="${line%%=*}"
    value="${line#*=}"
    value="${value%$'\r'}"
    value="${value#\'}"
    value="${value%\'}"
    value="${value#\"}"
    value="${value%\"}"
    [[ -n "$value" ]] || continue

    if [[ "$value" =~ $GENERATED_PLACEHOLDER ]]; then
        echo "  ${name}: still a placeholder; run setup-env.sh" >&2
        failures=$((failures + 1))
        continue
    fi

    digest=$(printf '%s=%s' "$name" "$value" | openssl dgst -sha256 | awk '{print $NF}')
    if grep -qxF "$digest" <<<"$PUBLISHED_SHA256"; then
        echo "  ${name}: published in the repository's .env.dev" >&2
        failures=$((failures + 1))
    fi
done <"$ENV_FILE"

if [[ "$failures" -gt 0 ]]; then
    echo "ERROR: ${ENV_FILE} holds ${failures} secret(s) that are public or never generated." >&2
    echo "       Rotate each one: set a new random value in ${ENV_FILE} and in the service that stores it" >&2
    echo "       (a database password also lives inside the database), then restart the stack." >&2
    exit 1
fi

echo "OK: ${ENV_FILE} holds no published or placeholder secret."
