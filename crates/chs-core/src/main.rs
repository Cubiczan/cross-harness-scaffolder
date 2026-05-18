use chs_core::{
    build_directory_manifest, load_session_config, run_consensus_report, sign_manifest_hmac,
    validate_session_config,
};
use std::env;
use std::fs;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args().skip(1);
    let Some(command) = args.next() else {
        print_help();
        std::process::exit(2);
    };

    match command.as_str() {
        "validate-config" => {
            let path = required_arg(args.next(), "config path")?;
            let session = load_session_config(path)?;
            let result = validate_session_config(&session);
            println!("{}", serde_json::to_string_pretty(&result)?);
            std::process::exit(if result.ok() { 0 } else { 1 });
        }
        "consensus-report" => {
            let path = required_arg(args.next(), "config path")?;
            let payload_id = args.next().unwrap_or_else(|| "CI0001".to_string());
            let session = load_session_config(path)?;
            let report = run_consensus_report(&session, &payload_id);
            println!("{}", report.render_markdown());
            std::process::exit(if report.passed() { 0 } else { 1 });
        }
        "sign-directory" => {
            let root = required_arg(args.next(), "bundle directory")?;
            let output = PathBuf::from(required_arg(args.next(), "manifest output path")?);
            let key_id = args.next().unwrap_or_else(|| "local".to_string());
            let secret_env = args.next().unwrap_or_else(|| "CHS_SIGNING_KEY".to_string());
            let secret = env::var(&secret_env)
                .map_err(|_| format!("missing signing secret env var: {secret_env}"))?;
            let manifest = build_directory_manifest(root, "chs-core")?;
            let signed = sign_manifest_hmac(&manifest, &secret, &key_id)?;
            if let Some(parent) = output.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::write(output, serde_json::to_string_pretty(&signed)?)?;
        }
        _ => {
            print_help();
            std::process::exit(2);
        }
    }
    Ok(())
}

fn required_arg(value: Option<String>, label: &str) -> Result<String, String> {
    value.ok_or_else(|| format!("missing {label}"))
}

fn print_help() {
    eprintln!(
        "Usage:
  chs-core validate-config <config.yaml|config.json>
  chs-core consensus-report <config.yaml|config.json> [payload-id]
  chs-core sign-directory <bundle-dir> <manifest-output> [key-id] [secret-env]"
    );
}
