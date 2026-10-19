# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-19 | SQLite com documentos JSON por entidade, chave composta coleção/id e sequências persistentes | permite evoluir entidades sem reconstruir a base; transação abrange toda operação HTTP e RLock serializa acesso compartilhado | estado apenas em memória ou arquivo JSON sem transação |
| 2026-10-19 | Separar store.py, domain.py e server.py; não criar respostas fictícias para rotas futuras | checkpoint verificável da base, reutilização das regras na futura conversa | implementar stubs que retornam listas vazias para passar verificações superficiais |

| 2026-10-19 13:54 -0300 | Guardar matricula_id, fim e modalidade na reserva e usar Classes sob a transação HTTP existente | devolver crédito à matrícula consumida e preservar dados da reserva; mesma regra reutilizável no chat | selecionar matrícula atual ao devolver crédito ou duplicar regras no transporte |

| 2026-10-19 13:56 -0300 | Attendance separado, relógio explícito por rodada e fim persistido da reserva para presença automática | preservar isolamento do relógio e aulas já reservadas após edição da grade; reutilizar trava HTTP e caixa de saída | alterar ambiente/global do relógio ou recalcular término usando grade editada |

| 2026-10-19 14:00 -0300 | Training separado do dispatcher da conversa; ficha validada inteira antes de salvar, svg calculado no acesso | reaproveitar domínio em §11 sem furar ordem de decisão; preservar ficha anterior em erro e fichas com exercícios desativados | chat parcial ou persistir campo svg desatualizado |

| 2026-10-19 14:04 -0300 | SVGs com interpolação CSS de caminhos articulados e transform da cabeça/equipamentos; HTML em template local escapado | movimento específico por exercício, sem SMIL/dependências; textos vêm do catálogo e não entram como markup | gerador de imagens, desenho único repetido ou HTML cadastrado sem escape |

| 2026-10-19 14:07 -0300 | Evaluations separado, usando transação HTTP e Classes.occurrence; conflitos semiabertos e escolha por id | reutilizar agenda real e garantir exclusividade concorrente sem nova infraestrutura | duplicar grade ou criar chat parcial para testes transversais |

| 2026-10-19 14:11 -0300 | Conversation reutiliza domínios e transação HTTP, guarda fluxo/opções por telefone e histórico separado da caixa automática | persistência e confirmação usam regras reais; suspensão humana segue §21, com exceção de saúde | duplicar regras de reserva ou misturar respostas diretas em /saida |

| 2026-10-19 14:15 -0300 | Privacy separa exportação/anonimização; Raio-X usa report único na API/CLI e substituição de arquivo temporário | preservar agregados e campos não medidos, limpar cópias operacionais sem ofertas de espera | duplicar cálculo CLI ou chamar cancelamento comum com oferta automática |

| 2026-10-19 14:20 -0300 | Backup ZIP com snapshot SQLite e academia.json; restauração lê apenas membros conhecidos e valida antes de substituir | cópia consistente online e recuperação da configuração em diretório novo sem extração de caminhos arbitrários | copiar SQLite/WAL em uso ou restaurar sem configuração |
