use std::char::REPLACEMENT_CHARACTER;
use std::str;

use bitflags::bitflags;
use chrono::DateTime;
use chrono::FixedOffset;
use chrono::TimeZone;

use nom::character::is_hex_digit;
use nom::{
    bytes::streaming::{tag, take_while_m_n},
    character::streaming::one_of,
    combinator::{map, map_res},
    multi::{count, fold_many_m_n},
    sequence::tuple,
    IResult,
};

#[derive(Debug, PartialEq, Eq)]
pub struct SMSDeliver {
    pub smsc: String,
    pub time: DateTime<FixedOffset>,
    pub sender: String,
    pub text: String,
}

#[derive(Debug, PartialEq, Eq)]
pub enum PDU {
    // SMSSubmit,
    SMSDeliver(SMSDeliver),
}

bitflags! {
    struct TypeOfMessage : u8 {
        const IS_SUBMIT_TYPE = 0x01;  // zero if deliver type

        // for submit type
        const REPLY_PATH_EXISTS = 0x80;
        const USER_DATA_HEADER_EXISTS = 0x40;
        const STATUS_REPORT_REQUESTED = 0x20;
        const DO_NOT_REJECT_DUPLICATES = 0x4;

        const VALIDITY_PERIOD_MASK = 0x18;
        const VALIDITY_PERIOD_NONE = 0x0;
        const VALIDITY_PERIOD_ENHANCED= 0x8;
        const VALIDITY_PERIOD_RELATIVE = 0x10;
        const VALIDITY_PERIOD_ABSOLUTE = 0x18;

        // for deliver type
        const STATUS_REPORT_INDICATION = 0x20;
        const MORE_MESSAGES_TO_SEND = 0x4;
    }

    struct DataCodingScheme : u8 {
        const IS_8BIT = 0x4;
        const IS_UCS2 = 0x8;
    }
}

fn octet(s: &[u8]) -> IResult<&[u8], u8> {
    map_res(take_while_m_n(2, 2, is_hex_digit), |i: &[u8]| {
        u8::from_str_radix(str::from_utf8(i).unwrap(), 16)
    })(s)
}

fn address(digits: usize) -> impl FnMut(&[u8]) -> IResult<&[u8], String> {
    move |s: &[u8]| {
        let (s, tof) = octet(s)?;
        let n = (digits >> 1) + (digits & 1);
        let (s, (_endpos, mut num)) = fold_many_m_n(
            n * 2,
            n * 2,
            one_of("0123456789F"),
            || (0, vec!['F'; n * 2 + 1]),
            |(i, mut vec), v| {
                vec[(i ^ 1) + 1] = v;
                (i + 1, vec)
            },
        )(s)?;

        if tof == 145 {
            num[0] = '+';
        }

        let rst: String = num.into_iter().filter(|&c| c != 'F').collect();

        Ok((s, rst))
    }
}

fn parse_smsc(s: &[u8]) -> IResult<&[u8], String> {
    let (s, len) = octet(s)?;
    let len = len as usize;
    let digits = (len - 1) * 2;
    let (s, num) = address(digits)(s)?;
    Ok((s, num))
}

struct SmsDeliverPart {
    pub time: DateTime<FixedOffset>,
    pub sender: String,
    pub text: String,
}

fn dec_to_u32(v: u8) -> u32 {
    ((v & 0xF) * 10 + (v >> 4)) as u32
}

fn tp_scts(s: &[u8]) -> IResult<&[u8], DateTime<FixedOffset>> {
    let (s, v) = count(map(octet, dec_to_u32), 7)(s)?;
    let tz = v[6] as i32;
    let tz = if tz > 12 * 4 { tz - 24 * 4 } else { tz };

    Ok((
        s,
        FixedOffset::east(3600 / 4 * tz)
            .ymd(2000 + v[0] as i32, v[1], v[2])
            .and_hms(v[3], v[4], v[5]),
    ))
}

fn unichar(s: &[u8]) -> IResult<&[u8], u16> {
    map_res(take_while_m_n(4, 4, is_hex_digit), |i: &[u8]| {
        u16::from_str_radix(str::from_utf8(i).unwrap(), 16)
    })(s)
}

fn ud_ucs2(length: u8) -> impl FnMut(&[u8]) -> IResult<&[u8], String> {
    let length = length as usize;
    move |s: &[u8]| -> IResult<&[u8], String> {
        let (s, ud) = fold_many_m_n(
            length / 2,
            length / 2,
            unichar,
            || Vec::<u16>::with_capacity(length / 2),
            |mut acc, v| {
                acc.push(v);
                acc
            },
        )(s)?;
        let rst: String = char::decode_utf16(ud)
            .map(|r| r.unwrap_or(REPLACEMENT_CHARACTER))
            .collect();
        Ok((s, rst))
    }
}

const GSM_7BIT: [char; 128] = [
    '@', '£', '$', '¥', 'è', 'é', 'ù', 'ì', 'ò', 'Ç', '\n', 'Ø', 'ø', '\r', 'Å', 'å', 'Δ', '_',
    'Φ', 'Γ', 'Λ', 'Ω', 'Π', 'Ψ', 'Σ', 'Θ', 'Ξ', ' ', 'Æ', 'æ', 'ß', 'É', ' ', '!', '"', '#', '¤',
    '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
    '8', '9', ':', ';', '<', '=', '>', '?', '¡', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'Ä', 'Ö', 'Ñ',
    'Ü', '§', '¿', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
    'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'ä', 'ö', 'ñ', 'ü', 'à',
];

fn gsm7_ext(v: u8) -> char {
    match v {
        10 => '\n',
        20 => '^',
        40 => '{',
        41 => '}',
        47 => '\\',
        60 => '[',
        61 => '~',
        62 => ']',
        64 => '|',
        101 => '€',
        _ => '?',
    }
}

fn ud_default(length: u8) -> impl FnMut(&[u8]) -> IResult<&[u8], String> {
    let length = length as usize;
    let bits = length * 7;
    let octets = bits / 8 + (bits % 8 > 0) as usize;
    move |s: &[u8]| -> IResult<&[u8], String> {
        let (s, (i, mut ud, rest)) = fold_many_m_n(
            octets,
            octets,
            octet,
            || (0, Vec::<u64>::with_capacity(21), 0u64),
            |(i, mut acc, mut cur), v| {
                if i % 7 == 0 && i != 0 {
                    acc.push(cur);
                    cur = 0;
                }
                cur |= (v as u64) << (8 * (i % 7));
                (i + 1, acc, cur)
            },
        )(s)?;

        ud.push(rest);
        assert_eq!(octets, i);

        let mut cur: u64 = 0;
        let mut it = ud.into_iter();
        let mut rst = String::with_capacity(length);
        let mut ext = false;

        for i in 0..length {
            if i % 8 == 0 {
                cur = it.next().unwrap();
            }

            let chr = (cur & 0x7F) as u8;
            cur >>= 7;
            match (chr, ext) {
                (c, true) => {
                    ext = false;
                    rst.push(gsm7_ext(c));
                }
                (27, false) => {
                    ext = true;
                }
                (c, _) => {
                    ext = false;
                    rst.push(GSM_7BIT[c as usize]);
                }
            };
        }

        Ok((s, rst))
    }
}

fn sms_deliver(s: &[u8]) -> IResult<&[u8], SmsDeliverPart> {
    let (s, l) = octet(s)?;
    let (s, (sender, _pid, dcs, time, udl)) = tuple((
        address(l as usize),
        tag("00"),
        map(octet, DataCodingScheme::from_bits_truncate),
        tp_scts,
        octet,
    ))(s)?;

    if dcs.contains(DataCodingScheme::IS_UCS2) {
        let (s, text) = ud_ucs2(udl)(s)?;
        Ok((s, SmsDeliverPart { time, sender, text }))
    } else {
        let (s, text) = ud_default(udl)(s)?;
        Ok((s, SmsDeliverPart { time, sender, text }))
    }
}

pub fn parse_pdu(s: &[u8]) -> IResult<&[u8], PDU> {
    let (s, (smsc, tom)) = tuple((parse_smsc, map(octet, TypeOfMessage::from_bits_truncate)))(s)?;
    match tom.contains(TypeOfMessage::IS_SUBMIT_TYPE) {
        true => todo!(),
        false => {
            let (s, part) = sms_deliver(s)?;
            Ok((
                s,
                PDU::SMSDeliver(SMSDeliver {
                    smsc: smsc,
                    time: part.time,
                    sender: part.sender,
                    text: part.text,
                }),
            ))
        }
    }
}

// ----------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_sms_deliver_ucs2() {
        let (_, rst) = parse_pdu(
            b"0891683110102105F0040D91688116728494F90008226091908561230C62117684732B53EB5C0F6A59",
        )
        .unwrap();

        assert_eq!(
            rst,
            PDU::SMSDeliver(SMSDeliver {
                smsc: "+8613010112500".to_owned(),
                time: DateTime::parse_from_rfc3339("2022-06-19T09:58:16+08:00").unwrap(),
                sender: "+8618612748499".to_owned(),
                text: "我的猫叫小橙".to_owned(),
            })
        )
    }

    #[test]
    fn test_sms_deliver_default() {
        let (_, rst) = parse_pdu(
            b"07911326040000F0040B911346610089F60000208062917314080CC8F71D14969741F977FD07",
        )
        .unwrap();

        assert_eq!(
            rst,
            PDU::SMSDeliver(SMSDeliver {
                smsc: "+31624000000".to_owned(),
                time: DateTime::parse_from_rfc3339("2002-08-26T19:37:41-04:00").unwrap(),
                sender: "+31641600986".to_owned(),
                text: "How are you?".to_owned(),
            })
        );

        let (_, rst) = parse_pdu(
            b"0891683110102105F0040D91688116728494F900002260222273802310F4F29C0EDAA0CEF336A88CA76F52"
        ).unwrap();
        assert_eq!(
            rst,
            PDU::SMSDeliver(SMSDeliver {
                smsc: "+8613010112500".to_owned(),
                time: DateTime::parse_from_rfc3339("2022-06-22T22:37:08+08:00").unwrap(),
                sender: "+8618612748499".to_owned(),
                text: "test {gsm ext}".to_owned(),
            })
        );
    }
}
