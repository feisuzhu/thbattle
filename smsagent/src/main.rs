use std::io::{Read, Write};
use std::str;
use std::time::Duration;

use argparse::{ArgumentParser, Store};
use log::{debug, error, info};
use once_cell::sync::OnceCell;
use serde_derive::{Deserialize, Serialize};
use serial::unix::TTYPort;
use serial::SerialPort;

mod smste;

use smste::commands::{
    CNMIMessageType, CNMIMode, DeleteMessage, GetSubscriberNumber, HangUp, ReadMessage,
    SelectMessageFormat, SetNewMessageIndication,
};
use smste::events::{parse_event, Event};
use smste::pdu::SMSDeliver;

static CALLBACK: OnceCell<String> = OnceCell::new();
static TE_NUMBER: OnceCell<String> = OnceCell::new();

fn send(port: &mut TTYPort, command: impl Into<String>) -> Result<(), Box<dyn std::error::Error>> {
    let command = command.into();
    info!("Sending: {}", &command);
    port.write_all(command.as_bytes())?;
    port.write_all(b"\r\n")?;
    port.flush()?;
    Ok(())
}

#[derive(Serialize, Deserialize)]
struct CallbackPayload {
    time: String,
    sender: String,
    receiver: String,
    text: String,
}

fn handle_sms(sms: SMSDeliver) -> Result<(), Box<dyn std::error::Error>> {
    info!("Received: {:?}", &sms);
    let payload = CallbackPayload {
        time: sms.time.to_rfc3339(),
        sender: sms.sender,
        receiver: TE_NUMBER.get().unwrap().to_string(),
        text: sms.text,
    };
    let resp = ureq::post(CALLBACK.get().unwrap().as_ref())
        .set("Content-Type", "application/json")
        .send_string(serde_json::to_string(&payload).unwrap().as_ref())?;

    let ret = resp.into_string()?;
    debug!("Server response: {}", ret);
    Ok(())
}

fn handle(port: &mut TTYPort, ev: Event) -> Result<(), Box<dyn std::error::Error>> {
    info!("Got {:?}", &ev);
    match ev {
        Event::SMSArrived(v) => {
            // SIM800C does not support AT+CMGRD
            // send(port, TakeMessage(v.index))?;
            send(port, ReadMessage(v.index))?;
            send(port, DeleteMessage(v.index))?;
        }
        Event::SubscriberNumber(v) => {
            TE_NUMBER.set(v)?;
        }
        Event::SMS(v) => {
            handle_sms(v)?;
        }
        Event::Ring => {
            send(port, HangUp)?;
        }

        _ => (),
    };
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();

    let mut dev: String = "/dev/ttyUSB2".to_owned();
    let mut callback: String = "http://localhost:8000/.callbacks/sms-verification".to_owned();

    let mut subscriber: String = "".to_owned();

    {
        let mut parser = ArgumentParser::new();
        parser.refer(&mut dev).add_option(&["--serial"], Store, "");
        parser
            .refer(&mut callback)
            .add_option(&["--callback"], Store, "");
        parser
            .refer(&mut subscriber)
            .add_option(&["--subscriber"], Store, "");
        parser.parse_args_or_exit();
    }

    CALLBACK.set(callback)?;

    let mut port = serial::open(&dev)?;
    port.set_timeout(Duration::from_secs(10)).unwrap();
    info!("Serial port {} opened", dev);

    if subscriber.is_empty() {
        send(&mut port, GetSubscriberNumber)?;
    } else {
        TE_NUMBER.set(subscriber)?;
    }

    send(&mut port, SelectMessageFormat::PDU)?;
    send(
        &mut port,
        SetNewMessageIndication(CNMIMode::DirectOrDiscard, CNMIMessageType::SendIndicator),
    )?;

    let mut buf: Vec<u8> = vec![0; 512];
    let mut next: Option<Vec<u8>> = None;
    let mut tail: usize = 0;
    loop {
        if let Some(new) = next.take() {
            buf = new;
        }

        let v = match port.read(&mut buf[tail..]) {
            Ok(v) => v,
            Err(e) if e.kind() == std::io::ErrorKind::TimedOut => {
                continue;
            }
            Err(e) => return Err(e.into()),
        };

        tail += v;
        if tail == 0 {
            continue;
        }
        debug!(
            "Recv: {:?}",
            str::from_utf8(&buf[(tail - v)..tail]).unwrap_or("[NOT VALID UTF8]")
        );
        if tail == buf.len() {
            if tail > 16384 {
                panic!("Buffer overflow");
            }
            buf.resize(buf.len() * 2, 0);
            continue;
        }
        let mut s = &buf[..tail];
        loop {
            match parse_event(s) {
                Ok((s1, ev)) => {
                    s = s1;
                    if let Err(e) = handle(&mut port, ev) {
                        error!("Error calling handler: {}", e);
                    }
                }
                Err(e) if e.is_incomplete() => {
                    let should_swap = s.len() < buf.len();
                    if should_swap {
                        tail = s.len();
                        let mut new = vec![0u8; 512];
                        (&mut new[..tail]).copy_from_slice(s);
                        next = Some(new);
                    }
                    break;
                }
                Err(e) => {
                    panic!("Parse error: {}", e);
                }
            }
        }
    }
}
