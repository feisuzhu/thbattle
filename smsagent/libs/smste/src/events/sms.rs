use nom::branch::alt;
use nom::bytes::streaming::{is_a, is_not, tag};
use nom::character::streaming::{char as ch};
use nom::combinator::{map_opt, map_res};
use nom::sequence::{delimited, preceded, tuple};
use nom::IResult;

use crate::common::integer;
use crate::events::Event;
use crate::pdu::{parse_pdu, PDU};

#[derive(Debug, PartialEq, Eq)]
pub enum StorageType {
    Flash,
    Sim,
    StatusReport,
}

impl TryFrom<&[u8]> for StorageType {
    type Error = ();

    fn try_from(s: &[u8]) -> Result<Self, Self::Error> {
        match s {
            b"ME" => Ok(StorageType::Flash),
            b"MT" => Ok(StorageType::Flash),
            b"SM" => Ok(StorageType::Sim),
            b"SR" => Ok(StorageType::StatusReport),
            _ => Err(()),
        }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct SMSStorageIndex {
    pub storage: StorageType,
    pub index: i32,
}

pub(crate) fn parse_cmti(s: &[u8]) -> IResult<&[u8], Event> {
    let (s, _) = tag("+CMTI: ")(s)?;
    let (s, storage) = map_res(
        delimited(
            ch('"'),
            alt((tag("ME"), tag("MT"), tag("SM"), tag("SR"))),
            ch('"'),
        ),
        StorageType::try_from,
    )(s)?;
    let (s, index) = preceded(ch(','), integer::<i32>)(s)?;

    Ok((s, Event::SMSArrived(SMSStorageIndex { storage, index })))
}

pub(crate) fn parse_cmgr(s: &[u8]) -> IResult<&[u8], Event> {
    // +CMGR: 0,"",38
    // 0891683110102105F0040D91688116728494F90000226081320161231434B3AC1C2E87C562712C2CCB996963720C07
    // TODO: mode is discarded, this could be a useful data
    let (s, (_, _, _, pdu)) = tuple((
        alt((tag("+CMGR: "), tag("+CMGRD: "))),
        is_not("\r\n"),
        is_a("\r\n"),
        map_opt(parse_pdu, |pdu| match pdu {
            PDU::SMSDeliver(v) => Some(v),
            _ => None,
        }),
    ))(s)?;
    Ok((s, Event::SMS(pdu)))
}
