# Настройка домашнего сервера MSI Cubi 5 12M с Ubuntu 26.04 LTS

Документ описывает установку и первичную защиту MSI Cubi 5 12M с 32 ГБ DDR4 и 1 ТБ NVMe под Ubuntu Server 26.04 LTS. Цель - локальный сервер для проектов на Podman Compose, опубликованных через Cloudflare Tunnel на домашнем или офисном подключении ByFly в Беларуси.

Подход по умолчанию:

- входящий трафик на роутере и сервере закрыт;
- проброс портов на роутере не используется;
- SSH-сервер не устанавливается и не используется удаленно;
- проекты разворачиваются физически через USB-носитель;
- Cloudflare Tunnel работает как исходящее соединение с сервера;
- до покупки домена используется только временный Cloudflare Quick Tunnel.

## 1. Важные ограничения

Cloudflare Tunnel без собственного домена подходит только для тестов. Временный режим TryCloudflare/Quick Tunnel выдает случайный адрес вида `https://*.trycloudflare.com`; Cloudflare прямо указывает, что этот режим предназначен для разработки и тестирования, а не для production. После покупки домена нужно добавить домен в Cloudflare DNS и создать обычный remotely-managed tunnel с публичным hostname.

Схема до покупки домена:

```text
Пользователь
  -> случайный *.trycloudflare.com URL
  -> Cloudflare Quick Tunnel
  -> исходящее соединение cloudflared с MSI Cubi
  -> http://127.0.0.1:<порт проекта>
```

Схема после покупки домена:

```text
Пользователь
  -> https://project.example.com
  -> Cloudflare DNS / TLS / WAF / rate limiting
  -> Cloudflare Tunnel
  -> исходящее соединение cloudflared с MSI Cubi
  -> http://127.0.0.1:<порт проекта>
  -> контейнеры Podman Compose
```

ByFly, динамический IP и возможный CG-NAT не мешают такой схеме, потому что сервер сам открывает исходящее соединение к Cloudflare. Белый статический IP и port forwarding не нужны.

## 2. Что подготовить заранее

Скачайте Ubuntu Server 26.04 LTS `amd64` с официальной страницы Ubuntu Server или с `https://releases.ubuntu.com/`. MSI Cubi 5 12M использует 64-битную Intel-платформу, поэтому нужен именно `amd64` server install image.

Проверьте ISO перед записью на флешку:

```bash
cd ~/Downloads
gpg --keyid-format long --verify SHA256SUMS.gpg SHA256SUMS
sha256sum -c SHA256SUMS 2>&1 | grep 'ubuntu-26.04.*server.*amd64.*OK'
```

Если проверка не дает `OK`, скачайте ISO заново. Не устанавливайте систему с непроверенного образа.

Подготовьте:

- USB-флешку 8 ГБ или больше для установщика Ubuntu;
- отдельный USB-носитель для деплоя проектов;
- монитор, клавиатуру и Ethernet-кабель;
- доступ к веб-интерфейсу роутера ByFly/ONT;
- надежный пароль для пользователя Ubuntu;
- отдельные пароли/секреты для `.env` проектов;
- источник бесперебойного питания, если сервер будет важен постоянно.

Для деплойной флешки лучше использовать шифрование. Минимальный вариант - хранить секреты не в репозитории, а в отдельном зашифрованном архиве. Более надежный вариант - LUKS/VeraCrypt-носитель, который не остается постоянно подключенным к серверу.

## 3. BIOS/UEFI на MSI Cubi

Подключите монитор, клавиатуру, Ethernet и питание. При включении обычно:

- `Del` открывает BIOS/UEFI Setup;
- `F11` открывает boot menu.

Если клавиши отличаются, ориентируйтесь на подсказку на первом экране MSI.

В BIOS сделайте следующее:

1. Загрузите `Optimized Defaults`.
2. Если BIOS сильно устарел, обновите его через официальный MSI support/M-FLASH. Не обновляйте BIOS во время нестабильного питания.
3. Включите `UEFI Only`; отключите `CSM/Legacy Boot`, если есть такая настройка.
4. Оставьте или включите `Secure Boot`. Если Ubuntu не загружается после установки, временно отключите Secure Boot и разберитесь отдельно.
5. Включите `TPM`/`fTPM`/`Intel PTT`, если настройка доступна.
6. Включите `Intel Virtualization Technology` и `VT-d`. Для Podman это не обязательно, но полезно для будущих VM.
7. Убедитесь, что NVMe-диск на 1 ТБ виден в BIOS.
8. Для SATA, если есть выбор, используйте `AHCI`.
9. Отключите PXE/network boot после установки, если он не нужен.
10. Отключите Wi-Fi и Bluetooth в BIOS, если сервер будет работать только по Ethernet.
11. Отключите Thunderbolt или выставьте максимально строгий security mode, если Thunderbolt не нужен.
12. Настройте восстановление после потери питания:
    - `Power On` - сервер сам включится после аварии питания;
    - `Last State` - вернется в прежнее состояние.
13. Установите BIOS administrator/supervisor password и сохраните его офлайн.
14. На время установки поставьте USB первым в boot order или используйте `F11`.

BIOS-пароль не защищает от всех атак при физическом доступе, но снижает риск случайного или быстрого изменения boot settings.

## 4. Установка Ubuntu Server 26.04 LTS

Загрузитесь с установочной флешки через `F11`.

Рекомендуемые ответы установщика:

- язык установщика: можно выбрать English, чтобы системные сообщения и ошибки было проще искать;
- клавиатура: нужная вам раскладка;
- сеть: Ethernet через DHCP;
- proxy: пусто, если ByFly/ваша сеть не требует proxy;
- mirror: дефолтный или ближайший надежный mirror;
- OpenSSH: не устанавливать;
- snaps: не выбирать ничего лишнего.

### Разметка диска

Есть два разумных варианта.

Вариант A, более безопасный для данных на диске: `Use entire disk` + LVM + LUKS encryption, если установщик предлагает шифрование. Минус: после каждого полного выключения, аварии питания или reboot сервер остановится на вводе LUKS-пароля. Это нормально, если у вас всегда есть физический доступ.

Вариант B, более автономный: `Use entire disk` + LVM без шифрования. Минус: при краже диска данные и secrets защищены только правами файловой системы, а не криптографией. Этот вариант удобнее, если сервер должен сам вернуться в работу после отключения электричества.

Для домашнего сервера без удаленного SSH я бы выбрал вариант A, если вы готовы вручную вводить пароль после перезагрузок. Если uptime важнее, выбирайте вариант B и особенно внимательно относитесь к физической защите и бэкапам.

Профиль:

- hostname: например `cubi-prod-01`;
- пользователь администратора: не `admin`, не `root`, лучше обычное имя;
- пароль: длинная уникальная фраза.

После завершения установки извлеките флешку и перезагрузитесь.

## 5. Первичная проверка после установки

Войдите локально на консоли и проверьте базовое состояние:

```bash
lsb_release -a
uname -a
lsblk -f
free -h
df -h
ip address
timedatectl
```

Настройте часовой пояс:

```bash
sudo timedatectl set-timezone Europe/Minsk
sudo timedatectl set-ntp true
timedatectl
```

Обновите систему:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

После reboot снова войдите локально.

## 6. Базовые пакеты

Установите минимальный набор для эксплуатации, контейнеров, диагностики и обновлений:

```bash
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  gnupg \
  htop \
  jq \
  lsb-release \
  net-tools \
  openssl \
  podman \
  podman-compose \
  rsync \
  tmux \
  ufw \
  unattended-upgrades \
  uidmap \
  fuse-overlayfs \
  passt \
  netavark \
  aardvark-dns
```

Если `apt` не находит `podman` или `podman-compose`, включите Ubuntu `universe` repository и повторите установку:

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update
```

Проверьте версии:

```bash
podman --version
podman-compose --version
```

Если `podman-compose` отсутствует в репозитории Ubuntu 26.04, используйте `podman compose`, но помните: это wrapper над внешним compose provider. Для production лучше зафиксировать один способ запуска в документации каждого проекта.

## 7. Полностью отключить SSH

На экране установки OpenSSH не должен был устанавливаться. Проверьте это явно:

```bash
systemctl status ssh || true
systemctl status ssh.socket || true
ss -tulpn
```

Если SSH все же установлен:

```bash
sudo systemctl disable --now ssh.service ssh.socket 2>/dev/null || true
sudo apt purge -y openssh-server
sudo apt autoremove --purge -y
```

После этого снова проверьте слушающие порты:

```bash
ss -tulpn
```

На сервере не должно быть `0.0.0.0:22`, `[::]:22` или других неожиданных публичных listener'ов.

## 8. Пользователи и директории для проектов

Администраторский пользователь нужен для обслуживания системы. Контейнеры лучше запускать rootless от отдельного пользователя без sudo, например `apps`.

Создайте пользователя и директории:

```bash
sudo adduser --disabled-password --gecos "" apps
sudo loginctl enable-linger apps

sudo mkdir -p /srv/projects /srv/backups /srv/incoming-usb
sudo chown apps:apps /srv/projects /srv/backups
sudo chmod 750 /srv/projects /srv/backups
sudo chmod 755 /srv/incoming-usb
```

Проверьте subuid/subgid для rootless Podman:

```bash
grep '^apps:' /etc/subuid /etc/subgid
```

Если записей нет, добавьте:

```bash
echo 'apps:100000:65536' | sudo tee -a /etc/subuid
echo 'apps:100000:65536' | sudo tee -a /etc/subgid
```

Проверьте rootless Podman:

```bash
sudo -iu apps podman info
```

Не отключайте `kernel.unprivileged_userns_clone`: rootless Podman зависит от user namespaces.

## 9. Фаервол UFW

Так как SSH не используется, входящих разрешающих правил не нужно.

Включите UFW:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw logging on
sudo ufw enable
sudo ufw status verbose
```

Проверьте, что IPv6 тоже включен в UFW:

```bash
grep '^IPV6=' /etc/default/ufw
```

Ожидаемо:

```text
IPV6=yes
```

Если там `no`, поменяйте на `yes` и перезапустите UFW:

```bash
sudo sed -i 's/^IPV6=.*/IPV6=yes/' /etc/default/ufw
sudo ufw disable
sudo ufw enable
sudo ufw status verbose
```

Не открывайте порты приложения наружу. В compose-файлах публикуйте сервисы только на loopback, например:

```yaml
ports:
  - "127.0.0.1:3001:3000"
```

Проверка:

```bash
ss -tulpn
```

Порты проектов должны слушать `127.0.0.1:<порт>`, а не `0.0.0.0:<порт>`.

## 10. Роутер ByFly/ONT

В веб-интерфейсе роутера:

1. Смените пароль администратора роутера.
2. Отключите remote administration со стороны интернета.
3. Отключите UPnP, если он не нужен.
4. Не включайте DMZ.
5. Не создавайте port forwarding на сервер.
6. Закрепите за сервером постоянный DHCP lease по MAC-адресу.
7. Обновите прошивку роутера, если оператор или производитель дает безопасный официальный способ.
8. Если Wi-Fi роутера используется, включите WPA2/WPA3 и длинный пароль.

Cloudflare Tunnel должен работать и за NAT, и за CG-NAT. Главное, чтобы сервер мог устанавливать исходящие соединения.

Проверка доступности Cloudflare Tunnel endpoints:

```bash
sudo apt install -y dnsutils netcat-openbsd
dig A region1.v2.argotunnel.com
nc -vz region1.v2.argotunnel.com 7844
nc -vz region2.v2.argotunnel.com 7844
```

Если TCP 7844 недоступен, проверьте роутер, фильтры провайдера и локальный firewall. При обычной настройке UFW с `allow outgoing` сервер сам ничего не блокирует.

## 11. Автоматические security updates

Ubuntu обычно включает security updates через `unattended-upgrades`, но это лучше проверить явно:

```bash
sudo apt install -y unattended-upgrades
cat /etc/apt/apt.conf.d/20auto-upgrades
```

Ожидаемая базовая конфигурация:

```text
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```

Для сервера с LUKS-шифрованием не включайте автоматическую перезагрузку: после reboot потребуется физический ввод пароля. Проверьте `/etc/apt/apt.conf.d/50unattended-upgrades`:

```text
Unattended-Upgrade::Automatic-Reboot "false";
```

Проверка pending reboot:

```bash
test -f /var/run/reboot-required && cat /var/run/reboot-required || true
```

Раз в неделю или месяц планово подключайтесь физически, обновляйте систему и перезагружайте:

```bash
sudo apt update
sudo apt full-upgrade -y
test -f /var/run/reboot-required && sudo reboot
```

## 12. Дополнительное hardening

Проверьте AppArmor:

```bash
sudo systemctl status apparmor
sudo aa-status
```

AppArmor должен быть активен. Не отключайте его для Podman без конкретной причины.

Отключите Bluetooth, если он не нужен:

```bash
sudo systemctl disable --now bluetooth 2>/dev/null || true
rfkill list || true
```

Если Wi-Fi не используется, лучше отключить его в BIOS. Если отключаете через ОС:

```bash
sudo rfkill block wifi
sudo rfkill block bluetooth
```

Добавьте аккуратные sysctl-настройки, которые не ломают rootless Podman:

```bash
sudo tee /etc/sysctl.d/99-local-hardening.conf >/dev/null <<'EOF'
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.unprivileged_bpf_disabled = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
EOF
sudo sysctl --system
```

Ограничьте размер persistent logs:

```bash
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/limits.conf >/dev/null <<'EOF'
[Journal]
SystemMaxUse=1G
MaxRetentionSec=30day
EOF
sudo systemctl restart systemd-journald
```

Периодически смотрите активные службы:

```bash
systemctl --type=service --state=running
ss -tulpn
```

Удаляйте пакеты и службы, которые реально не используете. Не добавляйте сторонние apt-репозитории без необходимости.

## 13. Установка cloudflared

Установить `cloudflared` можно прямо на сервере или принести `.deb` через флешку.

Вариант с загрузкой на сервере:

```bash
curl -L --output /tmp/cloudflared-linux-amd64.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo apt install -y /tmp/cloudflared-linux-amd64.deb
cloudflared --version
```

Вариант через флешку:

1. На доверенном компьютере скачайте `cloudflared-linux-amd64.deb` с официальной страницы Cloudflare Downloads.
2. Скопируйте файл на деплойную флешку.
3. На сервере установите:

```bash
sudo apt install -y /media/$USER/DEPLOY/cloudflared-linux-amd64.deb
cloudflared --version
```

Замените `DEPLOY` на фактическую метку USB-носителя, если она другая.

## 14. Временный запуск без домена: Quick Tunnel

Сначала убедитесь, что проект слушает локально, например:

```bash
curl -fsS http://127.0.0.1:3001/api/health || curl -I http://127.0.0.1:3001
```

Запустите временный tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:3001
```

`cloudflared` напечатает случайный URL на `trycloudflare.com`. Этот URL можно использовать для короткой проверки или демонстрации.

Ограничения Quick Tunnel:

- URL случайный и временный;
- режим не предназначен для production;
- нет нормальной DNS-привязки вашего hostname;
- не стоит публиковать там чувствительные формы и реальные пользовательские данные;
- после остановки процесса URL пропадет.

Для длительного теста можно держать процесс в `tmux`:

```bash
tmux new -s tunnel
cloudflared tunnel --url http://127.0.0.1:3001
```

Отсоединиться от `tmux`: `Ctrl-b`, затем `d`. Вернуться:

```bash
tmux attach -t tunnel
```

## 15. Production-схема после покупки домена

После покупки домена:

1. Добавьте домен в Cloudflare.
2. Смените nameservers у регистратора на Cloudflare nameservers.
3. В Cloudflare Zero Trust откройте `Networks` -> `Tunnels`.
4. Создайте remotely-managed tunnel.
5. Выберите Linux и скопируйте service install command.
6. На сервере выполните команду вида:

```bash
sudo cloudflared service install 'PASTE_TUNNEL_TOKEN_HERE'
sudo systemctl status cloudflared
```

7. В Routes/Published application добавьте hostname, например `risk.example.com`.
8. В `Service URL` укажите локальный адрес приложения, например:

```text
http://127.0.0.1:3001
```

9. Проверьте:

```bash
curl -fsS http://127.0.0.1:3001/api/health || curl -I http://127.0.0.1:3001
curl -I https://risk.example.com
```

Рекомендуемые edge-настройки Cloudflare для публичного проекта:

- TLS/HTTPS включен;
- Always Use HTTPS включен;
- WAF managed rules включены;
- rate limiting для чувствительных endpoint'ов, например `POST /api/waitlist`;
- Bot/Challenge controls включаются осторожно, чтобы не ломать обычных пользователей;
- Cloudflare Access включайте для приватных админских приложений, но не создавайте SSH-доступ, если принципиально не хотите удаленный SSH.

Токен tunnel считается секретом. Если он попал в чужие руки, удалите tunnel connector или перевыпустите token в Cloudflare.

## 16. Деплой проектов через USB

На сервере проекты лежат в `/srv/projects/project-name` и принадлежат пользователю `apps`.

Пример структуры:

```text
/srv/projects/
  bitcoin-risk-brief/
    podman-compose.yml
    .env
    backend/
    frontend/
```

### Вариант A: деплой исходников и сборка на сервере

Подготовьте проект на рабочем компьютере, скопируйте на флешку, подключите флешку к серверу и найдите устройство:

```bash
lsblk -f
```

Если автомонтирования нет:

```bash
sudo mkdir -p /mnt/deploy-usb
sudo mount /dev/sdX1 /mnt/deploy-usb
```

Скопируйте проект:

```bash
sudo rsync -a --delete /mnt/deploy-usb/bitcoin-risk-brief/ /srv/projects/bitcoin-risk-brief/
sudo chown -R apps:apps /srv/projects/bitcoin-risk-brief
sudo chmod 750 /srv/projects/bitcoin-risk-brief
sudo chmod 600 /srv/projects/bitcoin-risk-brief/.env
```

Запустите:

```bash
sudo -iu apps bash -lc 'cd /srv/projects/bitcoin-risk-brief && podman-compose up -d --build --remove-orphans'
sudo -iu apps podman ps
```

Проверьте локальный endpoint:

```bash
curl -fsS http://127.0.0.1:3001/api/health
```

### Вариант B: деплой готовых container images

Если не хотите собирать на сервере, соберите образ на доверенной машине:

```bash
podman build -t localhost/myproject:2026-06-30 .
podman save -o myproject-2026-06-30.tar localhost/myproject:2026-06-30
```

Скопируйте `.tar` на флешку, затем на сервере:

```bash
sudo -iu apps podman load -i /mnt/deploy-usb/myproject-2026-06-30.tar
```

В compose-файле используйте локальный image tag и не полагайтесь на pull из registry:

```yaml
services:
  app:
    image: localhost/myproject:2026-06-30
    pull_policy: never
    ports:
      - "127.0.0.1:3001:3000"
```

После обновления:

```bash
sudo -iu apps bash -lc 'cd /srv/projects/myproject && podman-compose up -d --remove-orphans'
```

## 17. Автозапуск Podman Compose проектов

Для каждого проекта создайте rootless systemd user service от имени `apps`.

Пример:

```bash
sudo -iu apps mkdir -p /home/apps/.config/systemd/user
sudo -iu apps tee /home/apps/.config/systemd/user/bitcoin-risk-brief.service >/dev/null <<'EOF'
[Unit]
Description=bitcoin-risk-brief Podman Compose stack
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/srv/projects/bitcoin-risk-brief
ExecStart=/usr/bin/podman-compose up -d --remove-orphans
ExecStop=/usr/bin/podman-compose down
RemainAfterExit=yes
TimeoutStartSec=900

[Install]
WantedBy=default.target
EOF

sudo -iu apps systemctl --user daemon-reload
sudo -iu apps systemctl --user enable --now bitcoin-risk-brief.service
sudo -iu apps systemctl --user status bitcoin-risk-brief.service
```

Если проект собирает образы на старте, первый запуск может быть долгим. `TimeoutStartSec=900` дает до 15 минут.

Логи:

```bash
sudo -iu apps journalctl --user -u bitcoin-risk-brief.service -e
sudo -iu apps bash -lc 'cd /srv/projects/bitcoin-risk-brief && podman-compose logs --tail=200'
```

## 18. Бэкапы

NVMe на 1 ТБ не заменяет бэкап. Минимальная схема:

- локальная копия на сервере для быстрых откатов;
- внешняя USB-копия, которая не подключена постоянно;
- периодическая проверка восстановления.

Для проекта `bitcoin-risk-brief` используйте штатный скрипт:

```bash
cd /srv/projects/bitcoin-risk-brief
./scripts/backup.sh
```

Потом скопируйте backup на внешний носитель:

```bash
sudo rsync -a /srv/projects/bitcoin-risk-brief/backups/ /mnt/deploy-usb/backups/bitcoin-risk-brief/
sync
sudo umount /mnt/deploy-usb
```

Для других проектов делайте отдельные database dumps и копии важных volumes. Не считайте бэкап рабочим, пока хотя бы один раз не проверили restore на отдельной копии.

## 19. Регулярное обслуживание

Раз в неделю:

```bash
sudo apt update
apt list --upgradable
test -f /var/run/reboot-required && cat /var/run/reboot-required || true
sudo ufw status verbose
ss -tulpn
sudo systemctl status cloudflared --no-pager
sudo -iu apps podman ps
sudo -iu apps podman system df
```

Раз в месяц:

```bash
sudo apt full-upgrade -y
sudo apt autoremove --purge -y
sudo journalctl --vacuum-time=30d
sudo reboot
```

Если включен LUKS, делайте monthly reboot только когда вы рядом с сервером и готовы ввести пароль.

## 20. Быстрое отключение публикации

Если нужно срочно убрать все проекты из публичного доступа:

```bash
sudo systemctl stop cloudflared
```

Если нужно остановить конкретный проект:

```bash
sudo -iu apps systemctl --user stop bitcoin-risk-brief.service
```

Если есть подозрение на утечку `.env` или Cloudflare token:

1. Остановите `cloudflared`.
2. Остановите проект.
3. Перевыпустите tunnel token в Cloudflare.
4. Смените пароли и API keys проекта.
5. Проверьте `ss -tulpn`, `podman ps`, логи приложения и Cloudflare events.

## 21. Финальный чеклист

Перед первым публичным запуском:

- BIOS обновлен только официальным способом и защищен administrator password.
- Boot mode: UEFI.
- Secure Boot включен или осознанно отключен с причиной.
- Wi-Fi/Bluetooth/Thunderbolt отключены, если не используются.
- Ubuntu Server 26.04 LTS установлена с проверенного ISO.
- OpenSSH server не установлен.
- UFW включен: deny incoming, allow outgoing.
- На роутере нет port forwarding, DMZ и remote admin.
- Проекты слушают только `127.0.0.1`.
- Podman запускает проекты rootless от пользователя `apps`.
- `.env` имеет права `600` и не хранится в git.
- `unattended-upgrades` включен.
- Есть внешний бэкап и проверенный restore-план.
- Quick Tunnel используется только временно.
- Для production куплен домен, добавлен в Cloudflare DNS, настроены WAF/rate limiting.

## 22. Полезные первоисточники

- Ubuntu Server documentation: `https://ubuntu.com/server/docs/`
- Ubuntu Server basic installation: `https://ubuntu.com/server/docs/tutorial/basic-installation/`
- Ubuntu ISO verification: `https://ubuntu.com/tutorials/how-to-verify-ubuntu`
- Ubuntu firewall/UFW: `https://ubuntu.com/server/docs/how-to/security/firewalls/`
- Ubuntu automatic updates: `https://ubuntu.com/server/docs/how-to/software/automatic-updates/`
- Ubuntu security suggestions: `https://ubuntu.com/server/docs/explanation/security/security_suggestions/`
- MSI Cubi 5 12M specifications: `https://www.msi.com/Business-Productivity-PC/Cubi-5-12M/Specification`
- Cloudflare Tunnel dashboard setup: `https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/`
- Cloudflare Quick Tunnels: `https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/`
- Cloudflare Tunnel firewall requirements: `https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-with-firewall/`
- Cloudflare cloudflared downloads: `https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/`
- Podman installation: `https://podman.io/docs/installation`
- Podman Compose wrapper: `https://docs.podman.io/en/latest/markdown/podman-compose.1.html`
- Podman Quadlet/systemd reference: `https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html`
