pub mod calling;
pub mod sms;

pub use self::calling::*;
pub use self::sms::*;

use std::str;

use nom::branch::alt;
use nom::bytes::streaming::{is_a, is_not, tag};
use nom::character::streaming::{char as ch, digit1, multispace0, one_of};
use nom::combinator::{map, opt, recognize};
use nom::sequence::{delimited, terminated, tuple};
use nom::IResult;

use super::pdu::SMSDeliver;

#[derive(Debug, Eq, PartialEq)]
pub enum Event {
    // General
    Ok,
    Error,
    NoCarrier,
    SubscriberNumber(String), // CNUM
    EchoedATCommand(String),

    // SMS
    SMSArrived(SMSStorageIndex), // CMTI
    SMS(SMSDeliver),             // CMGR, CMGRD

    // Voice
    Ring,
    CallIdentification(String),
    CurrentCall(CurrentCall),
    MissedCall(MissedCall),

    // bad or not impl
    Unrecognized(String),
}

fn parse_cnum(s: &[u8]) -> IResult<&[u8], Event> {
    // +CNUM: "","+8613263323935",145
    let (s, num) = delimited(
        tag("+CNUM: \"\","),
        delimited(ch('"'), recognize(tuple((opt(ch('+')), digit1))), ch('"')),
        ch(','),
    )(s)?;
    let (s, _) = digit1(s)?;

    Ok((
        s,
        Event::SubscriberNumber(String::from_utf8_lossy(num).into()),
    ))
}

fn parse_echoed_at_command(s: &[u8]) -> IResult<&[u8], Event> {
    map(
        recognize(tuple((tag("AT"), is_not("\r\n"), is_a("\r\n")))),
        |v: &[u8]| Event::EchoedATCommand(str::from_utf8(v).unwrap().trim().to_string()),
    )(s)
}

pub fn parse_event(s: &[u8]) -> IResult<&[u8], Event> {
    let (s, _) = multispace0(s)?;
    alt((
        map(terminated(tag("OK"), one_of("\r\n")), |_| Event::Ok),
        map(terminated(tag("ERROR"), one_of("\r\n")), |_| Event::Error),
        map(terminated(tag("NO CARRIER"), one_of("\r\n")), |_| {
            Event::NoCarrier
        }),
        parse_cnum,
        parse_cmti,
        parse_cmgr,
        parse_ring,
        parse_clip,
        parse_clcc,
        parse_missed_call,
        parse_echoed_at_command,
        map(terminated(is_not("\r\n"), one_of("\r\n")), |v: &[u8]| {
            Event::Unrecognized(String::from_utf8_lossy(v).into())
        }),
    ))(s)
}

#[cfg(test)]
mod tests {
    use chrono::{DateTime, NaiveTime};

    use crate::events::{CallDirection, CallMode, CurrentCall};
    use crate::events::{CallState, MissedCall, SMSStorageIndex, StorageType};
    use crate::pdu::SMSDeliver;

    use super::{parse_event, Event};

    #[test]
    fn test_parse_event() {
        let payload = r#"
OK
+CLCC: 2,0,2,0,0,"18612748499",129
NO CARRIER

+CMTI: "ME",1
+CMGR: 0,"",38
0891683110102105F0040D91688116728494F90000226081320161231434B3AC1C2E87C562712C2CCB996963720C07

+CMGRD: 0,"",32
0891683110102105F0040D91688116728494F90008226091908561230C62117684732B53EB5C0F6A59
+CSUB: B06V01
+CNUM: "","+8613263323935",145
+CRING: VOICE
+CLIP: "18612748499",161,,,,0
MISSED_CALL: 07:54PM 18612748499
AT+CMGF=0
OK
AT+CNMI=1,1
"#
        .replace("\n", "\r\r\n");
        let s = payload.as_ref();

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(v, Event::Ok);

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(
            v,
            Event::CurrentCall(CurrentCall {
                id: 2,
                direction: CallDirection::MobileOriginated,
                state: CallState::Dialing,
                mode: CallMode::Voice,
                is_multiparty: false,
                number: Some("18612748499".to_owned()),
            })
        );

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(v, Event::NoCarrier);

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(
            v,
            Event::SMSArrived(SMSStorageIndex {
                storage: StorageType::Flash,
                index: 1
            })
        );

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(
            v,
            Event::SMS(SMSDeliver {
                smsc: "+8613010112500".to_owned(),
                time: DateTime::parse_from_rfc3339("2022-06-18T23:10:16+08:00").unwrap(),
                sender: "+8618612748499".to_owned(),
                text: "4f2eaeabbb1a29f4cd18".to_owned(),
            })
        );

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(
            v,
            Event::SMS(SMSDeliver {
                smsc: "+8613010112500".to_owned(),
                time: DateTime::parse_from_rfc3339("2022-06-19T09:58:16+08:00").unwrap(),
                sender: "+8618612748499".to_owned(),
                text: "我的猫叫小橙".to_owned(),
            })
        );

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(v, Event::Unrecognized("+CSUB: B06V01".into()));

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(v, Event::SubscriberNumber("+8613263323935".into()));

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(v, Event::Ring);

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(v, Event::CallIdentification("18612748499".into()));

        let (s, v) = parse_event(s).unwrap();
        assert_eq!(
            v,
            Event::MissedCall(MissedCall {
                time: NaiveTime::from_hms_opt(19, 54, 00).unwrap(),
                number: "18612748499".into()
            })
        );

        let _ = s;
    }

    #[test]
    fn test_no_incomplete() {
        let s = b"\n\r\n+CMTI: \"ME\",4\r\n";
        let (_s, v) = parse_event(s).unwrap();
        assert_eq!(
            v,
            Event::SMSArrived(SMSStorageIndex {
                storage: StorageType::Flash,
                index: 4
            })
        );
    }
}
