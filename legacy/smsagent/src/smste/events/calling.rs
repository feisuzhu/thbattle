use chrono::NaiveTime;

use nom::branch::alt;
use nom::bytes::streaming::{is_not, tag};
use nom::character::streaming::{char as ch, digit1, one_of};
use nom::combinator::{map, opt, recognize};
use nom::sequence::{delimited, preceded, separated_pair, terminated, tuple};
use nom::IResult;
use num_derive::{FromPrimitive, ToPrimitive};

use super::Event;
use crate::smste::common::{int_enum, integer};

#[derive(FromPrimitive, ToPrimitive, Debug, PartialEq, Eq)]
pub enum CallDirection {
    MobileOriginated = 0,
    MobileTerminated = 1,
}

#[derive(FromPrimitive, ToPrimitive, Debug, PartialEq, Eq)]
pub enum CallState {
    Active = 0,
    Held = 1,
    Dialing = 2,
    Alerting = 3,
    Incoming = 4,
    Waiting = 5,
    Disconnect = 6,
}

#[derive(FromPrimitive, ToPrimitive, Debug, PartialEq, Eq)]
pub enum CallMode {
    Voice = 0,
    Data = 1,
    Fax = 2,
    Unknown = 9,
}

#[derive(Debug, PartialEq, Eq)]
pub struct CurrentCall {
    pub id: u32,
    pub direction: CallDirection,
    pub state: CallState,
    pub mode: CallMode,
    pub is_multiparty: bool,
    pub number: Option<String>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct MissedCall {
    // MISSED_CALL: 07:54PM 18612748499
    pub time: NaiveTime,
    pub number: String,
}

pub(crate) fn parse_missed_call(s: &[u8]) -> IResult<&[u8], Event> {
    let (s, (_, (hh, mm), noon, _, num)) = tuple((
        tag("MISSED_CALL: "),
        separated_pair(integer::<u32>, ch(':'), integer::<u32>),
        alt((tag("AM"), tag("PM"))),
        ch(' '),
        digit1,
    ))(s)?;

    let hh = match noon {
        b"AM" => hh,
        b"PM" => hh + 12,
        _ => unreachable!(),
    };

    Ok((
        s,
        Event::MissedCall(MissedCall {
            time: NaiveTime::from_hms_opt(hh, mm, 0).unwrap(),
            number: String::from_utf8_lossy(num).into(),
        }),
    ))
}

pub(crate) fn parse_clip(s: &[u8]) -> IResult<&[u8], Event> {
    // +CLIP:
    // <number>,<type>,,[,[<alpha>][,<CLI validity>]
    // +CLIP: "18612748499",161,,,,0
    let (s, _) = tag("+CLIP: ")(s)?;
    let (s, (num, _, _)) = tuple((
        delimited(ch('"'), recognize(tuple((opt(ch('+')), digit1))), ch('"')),
        is_not("\r\n"),
        one_of("\r\n"),
    ))(s)?;
    Ok((
        s,
        Event::CallIdentification(String::from_utf8_lossy(num).into()),
    ))
}

pub(crate) fn parse_clcc(s: &[u8]) -> IResult<&[u8], Event> {
    // +CLCC:<id1>,<dir>,<stat>,<mode>,<mpty>[,<number>,<type>[,alpha>]][<CR><LF>
    // +CLCC: 2,1,4,0,0,"18612748499",161
    let (s, (_, id, direction, state, mode, is_multiparty, number, _)) = tuple((
        tag("+CLCC: "),
        terminated(integer::<u32>, ch(',')),
        terminated(int_enum::<CallDirection>, ch(',')),
        terminated(int_enum::<CallState>, ch(',')),
        terminated(int_enum::<CallMode>, ch(',')),
        map(integer, |v: u32| v > 0),
        opt(terminated(
            preceded(ch(','), delimited(ch('"'), digit1, ch('"'))),
            is_not("\r\n"),
        )),
        one_of("\r\n"),
    ))(s)?;

    Ok((
        s,
        Event::CurrentCall(CurrentCall {
            id,
            direction,
            state,
            mode,
            is_multiparty,
            number: number.map(|v| String::from_utf8_lossy(v).into()),
        }),
    ))
}

pub(crate) fn parse_ring(s: &[u8]) -> IResult<&[u8], Event> {
    alt((
        map(
            tuple((tag("+CRING: "), is_not("\r\n"), one_of("\r\n"))),
            |_| Event::Ring,
        ),
        map(tag("RING"), |_| Event::Ring),
    ))(s)
}
