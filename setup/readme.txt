MyDroidDeck - servidor
======================

Transforma o seu Android em um "Stream Deck": o celular dispara acoes que o
servidor executa no PC. Esta pasta e a instalacao do servidor.


Iniciar / parar / reiniciar
---------------------------
Windows (menu Iniciar > MyDroidDeck):
  - Configuracao do MyDroidDeck   abre a pagina de configuracao no navegador
  - Iniciar servidor              liga o servidor (sem janela)
  - Parar servidor                desliga o servidor
  - Reiniciar servidor            desliga e liga de novo

  Ou, na pasta de instalacao:
    start.cmd   stop.cmd   restart.cmd   status.cmd

Linux / WSL:
    bin/mydroiddeck start | stop | restart | status
    bin/mydroiddeck open        (inicia se preciso e abre a configuracao)


Pagina de configuracao
----------------------
    http://127.0.0.1:56997/

A porta pode ser alterada na propria pagina (Configuracao > Porta). O endereco
abre sempre no Firefox configurado - nunca no navegador padrao do Windows.


Onde ficam os dados
-------------------
    data/    banco SQLite, runtime.json (porta / visivel na rede), icones
    logs/    server.log

"Visivel na rede" (LAN) tambem exige liberar a porta no firewall do Windows;
veja setup/README.md no repositorio.


Iniciar no logon
----------------
Marque a opcao durante a instalacao ou use o botao "Iniciar no logon" na pagina
de configuracao.


Desinstalar
-----------
Menu Iniciar > MyDroidDeck > Desinstalar MyDroidDeck.

Os dados em data/ sao mantidos para nao perder as configuracoes; apague a pasta
para remover tudo.
