import re

# Mapeamento de macros para códigos de escape EZTR
mapping = {
    "COLOR_DEFAULT": "|00",
    "COLOR_RED": "|01",
    "COLOR_GREEN": "|02",
    "COLOR_BLUE": "|03",
    "COLOR_YELLOW": "|04",
    "COLOR_LIGHTBLUE": "|05",
    "COLOR_PINK": "|06",
    "COLOR_SILVER": "|07",
    "COLOR_ORANGE": "|08",
    "BOX_BREAK": "|10",
    "BOX_BREAK2": "|12",
    "EVENT": "|19",
    "EVENT2": "|19",            # Tratado como EVENT
    "QUICKTEXT_ENABLE": "|17",
    "QUICKTEXT_DISABLE": "|18",
    "CARRIAGE_RETURN": ""
}

# Lê o arquivo message_data.h
with open('message_data.h', 'r', encoding='utf-8') as f:
    text = f.read()

# Função para processar um bloco DEFINE_MESSAGE
def process_define_block(block):
    # Extrai o ID da mensagem (primeiro argumento)
    m = re.match(r'\s*DEFINE_MESSAGE\(\s*(0x[0-9A-Fa-f]+)', block)
    if not m:
        return None, None
    text_id = m.group(1)
    # Encontra conteúdo dentro de MSG(...)
    msg_start = block.find('MSG(')
    if msg_start == -1:
        return text_id, ''
    i = msg_start + len('MSG(')
    depth = 1
    content = ''
    # Extrai até fechar MSG
    j = i
    while j < len(block) and depth > 0:
        if block[j] == '\"':
            # Pula literal de string
            j += 1
            while j < len(block):
                if block[j] == '\\\\':
                    j += 2
                elif block[j] == '\"':
                    j += 1
                    break
                else:
                    j += 1
        elif block[j] == '(':
            depth += 1
            j += 1
        elif block[j] == ')':
            depth -= 1
            j += 1
        else:
            j += 1
    content = block[i:j-1]  # Exclui ')' final
    # Processa o conteúdo, substituindo macros
    result = ''
    idx = 0
    while idx < len(content):
        ch = content[idx]
        if ch.isspace():
            idx += 1
            continue
        if ch == '\"':
            # Literal de string
            idx += 1
            lit = ''
            while idx < len(content):
                if content[idx] == '\\\\' and idx+1 < len(content) and content[idx+1] == 'n':
                    lit += '\\n'
                    idx += 2
                elif content[idx] == '\"':
                    idx += 1
                    break
                else:
                    lit += content[idx]
                    idx += 1
            # Substitui '\n' por código |11
            lit = lit.replace('\\n', '|11')
            result += lit
        elif content[idx].isalpha() or content[idx] == '_':
            # Token de macro ou controle
            start = idx
            while idx < len(content) and (content[idx].isalnum() or content[idx] == '_'):
                idx += 1
            token = content[start:idx]
            # Verifica chamada de macro com parâmetros
            if idx < len(content) and content[idx] == '(':
                depth2 = 1
                idx += 1
                while idx < len(content) and depth2 > 0:
                    if content[idx] == '(':
                        depth2 += 1
                    elif content[idx] == ')':
                        depth2 -= 1
                    elif content[idx] == '\"':
                        idx += 1
                        while idx < len(content) and content[idx] != '\"':
                            if content[idx] == '\\\\':
                                idx += 2
                            else:
                                idx += 1
                        # Fecha string interna
                    idx += 1
                # Macro com () é ignorado (como SFX, FADE, etc.)
            else:
                # Macro simples ou token isolado
                if token == 'TWO_CHOICE':
                    # Processa o bloco de opções TWO_CHOICE
                    while idx < len(content) and content[idx].isspace():
                        idx += 1
                    # Primeira opção
                    opt1 = ''
                    if idx < len(content) and content[idx] == '\"':
                        idx += 1
                        while idx < len(content):
                            if content[idx] == '\\\\' and idx+1 < len(content) and content[idx+1] == 'n':
                                idx += 2
                                break
                            elif content[idx] == '\"':
                                idx += 1
                                break
                            else:
                                opt1 += content[idx]
                                idx += 1
                    # Segunda opção
                    while idx < len(content) and content[idx].isspace():
                        idx += 1
                    opt2 = ''
                    if idx < len(content) and content[idx] == '\"':
                        idx += 1
                        while idx < len(content):
                            if content[idx] == '\\\\' and idx+1 < len(content) and content[idx+1] == 'n':
                                idx += 2
                                break
                            elif content[idx] == '\"':
                                idx += 1
                                break
                            else:
                                opt2 += content[idx]
                                idx += 1
                    # Adiciona sequência escape de escolha (|02|C2 etc.)
                    result += '|02|C2' + opt1 + '|11' + opt2
                elif token in mapping:
                    result += mapping[token]
                # Outros tokens são ignorados
        else:
            idx += 1
    return text_id, result

# Percorre todos os blocos DEFINE_MESSAGE
pos = 0
while True:
    idx = text.find('DEFINE_MESSAGE(', pos)
    if idx == -1:
        break
    # Encontra o fechamento correspondente
    depth = 1
    j = idx + len('DEFINE_MESSAGE(')
    while j < len(text) and depth > 0:
        if text[j] == '\"':
            j += 1
            while j < len(text) and text[j] != '\"':
                if text[j] == '\\\\':
                    j += 2
                else:
                    j += 1
            j += 1
        elif text[j] == '(':
            depth += 1
            j += 1
        elif text[j] == ')':
            depth -= 1
            j += 1
        else:
            j += 1
    block = text[idx:j]
    text_id, content = process_define_block(block)
    if text_id is not None:
        content = content + '|BF'
        # Escapa aspas duplas no conteúdo
        content = content.replace('"', '\\"')
        # Imprime chamada EZTR_Basic_ReplaceText
        print(f'EZTR_Basic_ReplaceText({text_id}, EZTR_STANDARD_TEXT_BOX_I, 1, EZTR_ICON_NO_ICON, EZTR_NO_VALUE, EZTR_NO_VALUE, EZTR_NO_VALUE, true, "{content}", NULL);')
    pos = j
