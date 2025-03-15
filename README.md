# htb-tools
scripts for HackTheBox / not for any other purpose / not production ready may contain bugs

## git-downloader

Tool used for HackTheBox boxes when the website has a `/.git/ folder, detected by nmap.

```mermaid
graph LR

a(find a website with a /.git/ folder) --> b(run tool) --> c(git reset --hard) --> d(look in the files, logs, branches, history)
```

