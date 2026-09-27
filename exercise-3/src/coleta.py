"""Download paginado das UBS na API de dados abertos do Ministério da Saúde."""
import time

import requests

import config


def baixar_ubs():
    """Percorre as páginas (limit/offset) até vir uma página vazia
    ou até atingir UBS_MAX_REGISTROS (0 = sem limite)."""
    registros = []
    offset = 0
    maximo = config.UBS_MAX_REGISTROS
    sessao = requests.Session()

    while True:
        limite = config.UBS_PAGE_SIZE
        if maximo > 0:
            limite = min(limite, maximo - len(registros))
            if limite <= 0:
                break

        params = {"limit": limite, "offset": offset}
        pagina = None
        # até 3 tentativas por página, caso a API oscile
        for tentativa in range(1, 4):
            try:
                resp = sessao.get(config.UBS_API_URL, params=params, timeout=60)
                resp.raise_for_status()
                pagina = resp.json().get("ubs", [])
                break
            except (requests.RequestException, ValueError) as erro:
                print(f"  offset={offset}: falha na tentativa {tentativa} ({erro})")
                time.sleep(2 * tentativa)
        if pagina is None:
            raise RuntimeError(f"Não foi possível baixar a página offset={offset}")

        if not pagina:  # página vazia = fim da base
            break

        registros.extend(pagina)
        offset += len(pagina)
        print(f"  offset={offset:>6} | acumulado: {len(registros)}")
        time.sleep(config.UBS_PAUSA)  # pausa para não sobrecarregar a API

    return registros
