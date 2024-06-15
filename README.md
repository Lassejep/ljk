# A Simple CLI Password Manager
This is a simple CLI password manager written in Python.
Run a server on a machine, access it from another machine through the client using a master password.
Store your passwords in an encrypted vault, and send them back to the server for storage.

## Requirements
- Python 3.6 or later
- Linux

If you want to use SSL, you need to have a certificate and key file, or openssl installed.

## Installation
```bash
git clone https://github.com/lassejep/ljk.git
cd ljk
pip install -r requirements.txt
python -m unittest
```
Make sure all tests pass before running the server and client.

## Usage
### SSL
If you want SSL enabled, and you don't have a certificate and key file, you can generate them with openssl using the following command.
```bash
openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout server.key -out server.crt
cat server.crt server.key > server.pem
```
Then simply fill out the information asked for.


This will generate a certificate and key file, and combine them into a single file.
When running the server you can use the `server.pem` file as the certificate.
Note that this is a self-signed certificate, and the private key is not protected by a password.
If you want to protect the private key with a password, you can remove the `-nodes` flag from the command above.

### Server
Run the server on a machine that you want to store your user database on.
```bash
python server.py -H <ip> -p <port> -d <database name> -l <log directory> -s <path to ssl certificate>
```
### Client
Run the client on a machine that you want to access your user database from.
```bash
python client.py -H <ip> -p <port>
```
The client should open a simple CLI interface where you can register, login, and store and retrieve passwords.

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
        f3 -->|Encrypt| evkey[Encrypted Vault Key]
    end
    subgraph Server
        evkey -->|Store| db[(Database)]
        evault -->|Store| db
    end
```
```mermaid
---
title: Login and Retrieve Vault
---
graph LR
    subgraph Client
        mpass{"Master \n Password"}
        mail1{Email}
        mail1 & mpass --> f1([Generate Data and Master Keys])
        f1 --> dkey[Data Key]
        f1 --> mkey[Master Key]
        evault2{Encrypted Vault} -->|Data| f4([AES-GCM])
        evkey2{Encrypted Vault Key} -->|Data| f3([AES-GCM])
        dkey -->|Encryption Key| f3
        f3 -->|Decrypt| vkey{"Vaultk Key"}
        vkey -->|Data| f4
        f4 -->|Decrypt| vault{Vault}
    end
    mail1 -->|Login Request| Server
    mkey -->|Login Request| Server
    subgraph Server
        mail2{Email} -->|Retrieve Auth Key| db[(Database)]
        mkey2{Master Key} -->|Data| f2([Argon2])
        f2 -->|Hash| akey[Auth Key]
        db --> akey2[Auth Key]
        akey2 -->|Compare| akey
        akey -->|Retrieve Encrypted data| db
        db -->|Data| evault[Encrypted Vault]
        db -->|Data| evkey[Encrypted Vault Key]
    end
        evault -->|Response| Client
        evkey -->|Response| Client
```
