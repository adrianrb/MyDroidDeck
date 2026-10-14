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
  - Conectar por USB              encaminha a porta pelo cabo (adb reverse)

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


Conectar o celular
------------------
Na instalacao voce escolhe como o celular alcanca este servidor (pode marcar
mais de uma opcao). A pagina de configuracao mostra os mesmos enderecos e o
botao "Conectar por USB".

  Wi-Fi / rede local
    Marque "Visivel na rede" e libere a porta no firewall do Windows (veja
    setup/README.md no repositorio). No app, leia o QR Code em
    Dispositivos > Parear novo.

  USB (cabo)
    Ligue o celular com a depuracao USB ativada e use o atalho "Conectar por
    USB" (ou tools\control.ps1 -Action usb-connect -Action usb-disconnect para
    desfazer). O equivalente em linha de comando, usando a porta configurada:

      adb reverse tcp:56997 tcp:56997

    No app, aponte o servidor para http://127.0.0.1:56997/ - nao precisa de
    rede. Precisa do adb (Android SDK platform-tools) neste PC.

  Bluetooth
    Ainda nao disponivel (previsto para uma proxima versao: o app falara com o
    servidor direto por Bluetooth).


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

O desinstalador para o servidor e pergunta se voce quer apagar tambem todos os
dados (perfis, dispositivos pareados, acoes, icones e logs). Responda "Nao" para
manter a pasta data/ com as suas configuracoes; responda "Sim" para remover tudo.
