use std::fs;
use std::process;

fn main() {
    /*
    process::Command::new("pb-rs")
        .arg("src/schema.proto")
        .status()
        .unwrap();
    fs::remove_file("src/mod.rs").unwrap();
    process::Command::new("rustfmt")
        .args(&["--edition", "2018"])
        .arg("src/schema.rs")
        .status()
        .unwrap();
    // */
}
