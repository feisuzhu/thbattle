use std::str::FromStr;

use nom::character::streaming::digit1;
use nom::combinator::{map_opt, map_res};
use nom::IResult;
use num_traits::FromPrimitive;

pub fn int_enum<T: FromPrimitive>(s: &[u8]) -> IResult<&[u8], T> {
    map_opt(digit1, |v: &[u8]| -> Option<T> {
        String::from_utf8_lossy(v)
            .parse::<u32>()
            .ok()
            .and_then(FromPrimitive::from_u32)
    })(s)
}

pub fn integer<T: FromStr>(s: &[u8]) -> IResult<&[u8], T> {
    map_res(digit1, |v: &[u8]| String::from_utf8_lossy(v).parse())(s)
}
