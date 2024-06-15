# A Simple CLI Password Manager
This is a simple CLI password manager written in Python.
Run a server on a machine, access it from another machine through the client using a master password.
Store your passwords in an encrypted vault, and send them back to the server for storage.

## Requirements
- Python 3.6 or later
- Linux

## Installation
```bash
git clone https://github.com/lassejep/ljk.git
cd ljk
pip install -r requirements.txt
python -m unittest
```
Make sure all tests pass before running the server and client.

## Usage
### Server
Run the server on a machine that you want to store your user database on.
```bash
python server.py --host <ip> -p <port> -d <database name> -l <log directory> -s <path to ssl certificate>
```
### Client
Run the client on a machine that you want to access your user database from.
```bash
python client.py --host <ip> -p <port> -s <path to ssl certificate>
```

## How it works
```mermaid
---
title: Create Data and Master Keys
---
graph LR
    subgraph Client
        direction LR
        mail{Email}
        mpass{"Master \n Password"}
        mpass -->|Data| f1([Argon2])
        mail -->|Salt| f1
        f1 -->|Hash| dkey[Data Key]
        mpass -->|Data| f2([Argon2])
        dkey -->|Salt| f2
        f2 -->|Hash| mkey[Master Key]
    end
```
```mermaid
---
title: Register
---
graph LR
    subgraph Client
        mail1{Email}
        mpass{"Master \n Password"}
        mail1 & mpass --> f1([Generate Data and Master Keys])
        f1 --> dkey[Data Key]
        f1 --> mkey1[Master Key]
    end
    mail1 --> r1([Register Request])
    mkey1 --> r1
    r1 -->|Register| Server
    subgraph Server
        mkey2{Master Key} -->|Data| f2([Argon2])
        mail2{Email} -->|Store| db[(Database)]
        f2 -->|Hash| akey[Auth Key]
        akey -->|Store| db[(Database)]
    end
```
```mermaid
---
title: Create and Store Vault
---
graph LR
    subgraph Client
    mail1{Email}
    mpass{"Master \n Password"}
    mail1 & mpass --> f1([Generate Data and Master Keys])
    f1 --> dkey[Data Key]
    f1 --> mkey[Master Key]
    vkey{"Vault Key \n (Random 256 bit key)"}
    vault{Vault}
    vkey -->|Encryption Key| f2([AES-GCM])
    vault -->|Data| f2
    f2 -->|Encrypt| evault[Encrypted Vault]
    vkey -->|Data| f3([AES-GCM])
    dkey -->|Encryption Key| f3
    f3 -->|Encrypt| edkey[Encrypted Vault Key]
end
    subgraph Server
    edkey -->|Store| db[(Database)]
    evault -->|Store| db
end
```
