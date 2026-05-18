//! Native Rust core for Cross-Harness Scaffolder.
//!
//! The Python CLI remains the broad integration surface. This crate owns the
//! deterministic, audit-sensitive primitives that benefit from Rust: config
//! validation, compact session state, consensus reports, payload envelopes, and
//! signed release-gate manifests.

use chrono::{SecondsFormat, Utc};
use hmac::{Hmac, Mac};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

type HmacSha256 = Hmac<Sha256>;

pub const PROTOCOL_VERSION: &str = "Cross-Harness Scaffolder v0.1.0";
pub const CANONICAL_PROTOCOL_NAME: &str = "Consensus Hardening Protocol";
pub const CANONICAL_PROTOCOL_URL: &str =
    "https://codeberg.org/cubiczan/consensus-hardening-protocol";
pub const MANIFEST_VERSION: &str = "chs-bundle-manifest-v1";
pub const TRANSPARENCY_LOG_VERSION: &str = "chs-transparency-log-v1";

#[derive(Debug, thiserror::Error)]
pub enum ChsError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("yaml error: {0}")]
    Yaml(#[from] serde_yaml::Error),
    #[error("unsupported config extension: {0}")]
    UnsupportedConfigExtension(String),
    #[error("signing secret is required")]
    MissingSigningSecret,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossHarnessLayer {
    RepoState,
    TaskFlow,
    SystemDesign,
    SecurityBoundary,
    BusinessRule,
    DeploymentContext,
}

impl CrossHarnessLayer {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::RepoState => "repo_state",
            Self::TaskFlow => "task_flow",
            Self::SystemDesign => "system_design",
            Self::SecurityBoundary => "security_boundary",
            Self::BusinessRule => "business_rule",
            Self::DeploymentContext => "deployment_context",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Verdict {
    Pass,
    Fail,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum IssueSeverity {
    Info,
    Warning,
    Critical,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HarnessRef {
    pub name: String,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub role: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DossierConfig {
    pub core_problem: String,
    #[serde(default)]
    pub goal_state: Vec<String>,
    #[serde(default)]
    pub current_state: Vec<String>,
    #[serde(default)]
    pub constraints: Vec<String>,
    #[serde(default)]
    pub scope: Vec<String>,
    #[serde(default)]
    pub origin_direction: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FoundationConfig {
    #[serde(default)]
    pub weakest_assumptions: Vec<String>,
    #[serde(default)]
    pub invalidation_conditions: Vec<String>,
    pub key_vulnerability: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiagnosticConfig {
    pub item: String,
    pub observed_layer: CrossHarnessLayer,
    pub constraint_layer: CrossHarnessLayer,
    pub diagnosis: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SessionConfig {
    pub title: String,
    pub origin: HarnessRef,
    pub partner: HarnessRef,
    #[serde(default)]
    pub validators: Vec<HarnessRef>,
    #[serde(default = "default_human_bridge")]
    pub human_bridge: String,
    pub dossier: DossierConfig,
    pub foundation: FoundationConfig,
    #[serde(default)]
    pub diagnostics: Vec<DiagnosticConfig>,
}

fn default_human_bridge() -> String {
    "Human operator".to_string()
}

impl SessionConfig {
    pub fn participant_count(&self) -> usize {
        2 + self.validators.len()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValidationIssue {
    pub path: String,
    pub message: String,
    pub severity: IssueSeverity,
}

impl ValidationIssue {
    fn error(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: IssueSeverity::Critical,
        }
    }

    fn warning(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: IssueSeverity::Warning,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValidationResult {
    pub issues: Vec<ValidationIssue>,
}

impl ValidationResult {
    pub fn ok(&self) -> bool {
        !self
            .issues
            .iter()
            .any(|issue| issue.severity == IssueSeverity::Critical)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ConsensusFinding {
    pub check: String,
    pub status: String,
    pub detail: String,
    pub severity: IssueSeverity,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ConsensusReport {
    pub verdict: Verdict,
    pub score: u8,
    pub findings: Vec<ConsensusFinding>,
}

impl ConsensusReport {
    pub fn passed(&self) -> bool {
        self.verdict == Verdict::Pass
    }

    pub fn render_markdown(&self) -> String {
        let mut lines = vec![
            "# Consensus Hardening Review".to_string(),
            String::new(),
            format!("Protocol: {CANONICAL_PROTOCOL_NAME}"),
            format!("Scaffolder: {PROTOCOL_VERSION}"),
            format!("Verdict: {:?}", self.verdict).to_uppercase(),
            format!("Score: {}", self.score),
            String::new(),
            "## Findings".to_string(),
            String::new(),
        ];
        for finding in &self.findings {
            lines.push(format!(
                "- {} | {} | {:?} | {}",
                finding.status, finding.check, finding.severity, finding.detail
            ));
        }
        lines.join("\n")
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PayloadEnvelope {
    pub route: String,
    pub payload_id: String,
    pub body: String,
}

impl PayloadEnvelope {
    pub fn render(&self) -> String {
        format!(
            "BEGIN_PAYLOAD [{}] [{}]\n{}\nEND_PAYLOAD [{}] [{}]",
            self.route,
            self.payload_id,
            ascii_only(&self.body),
            self.route,
            self.payload_id
        )
    }

    pub fn echo(&self) -> String {
        format!("[{}] [{}] CONFIRMED", self.route, self.payload_id)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompactSessionState {
    pub protocol_version: String,
    pub canonical_protocol: BTreeMap<String, String>,
    pub title: String,
    pub status: String,
    pub participant_count: usize,
    pub dossier_hash: String,
    pub diagnostics: Vec<String>,
    pub token_budget: BTreeMap<String, usize>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactEntry {
    pub path: String,
    pub purpose: String,
    pub content_hash: String,
    pub token_estimate: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BundleManifest {
    pub manifest_version: String,
    pub created_at: String,
    pub signer: String,
    pub artifact_count: usize,
    pub total_token_estimate: usize,
    pub artifacts: Vec<ArtifactEntry>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub signature: Option<ManifestSignature>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManifestSignature {
    pub algorithm: String,
    pub key_id: String,
    pub value: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TransparencyLogEntry {
    pub log_version: String,
    pub log_id: String,
    pub recorded_at: String,
    pub source: String,
    pub manifest_hash: String,
    pub manifest_version: String,
    pub manifest_created_at: String,
    pub signer: String,
    pub artifact_count: usize,
    pub signature_algorithm: String,
    pub signature_key_id: String,
    pub signature_value: String,
    pub previous_entry_hash: String,
    pub entry_hash: String,
}

pub fn load_session_config(path: impl AsRef<Path>) -> Result<SessionConfig, ChsError> {
    let path = path.as_ref();
    let text = fs::read_to_string(path)?;
    match path
        .extension()
        .and_then(|extension| extension.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase()
        .as_str()
    {
        "json" => Ok(serde_json::from_str(&text)?),
        "yaml" | "yml" => Ok(serde_yaml::from_str(&text)?),
        other => Err(ChsError::UnsupportedConfigExtension(other.to_string())),
    }
}

pub fn validate_session_config(session: &SessionConfig) -> ValidationResult {
    let mut issues = Vec::new();

    if session.title.trim().is_empty() {
        issues.push(ValidationIssue::error(
            "title",
            "must be a non-empty string",
        ));
    }
    validate_profile("origin", &session.origin, &mut issues);
    validate_profile("partner", &session.partner, &mut issues);
    for (idx, validator) in session.validators.iter().enumerate() {
        validate_profile(format!("validators[{idx}]"), validator, &mut issues);
    }
    if normalized(&session.origin.name) == normalized(&session.partner.name) {
        issues.push(ValidationIssue::warning(
            "partner.name",
            "origin and partner use the same harness family; add an independent validator",
        ));
    }
    if session.dossier.core_problem.trim().is_empty() || session.dossier.core_problem == "UNKNOWN" {
        issues.push(ValidationIssue::error(
            "dossier.core_problem",
            "must be a non-empty concrete problem",
        ));
    }
    for (path, value) in [
        ("dossier.goal_state", &session.dossier.goal_state),
        ("dossier.current_state", &session.dossier.current_state),
        ("dossier.constraints", &session.dossier.constraints),
        ("dossier.scope", &session.dossier.scope),
    ] {
        if value.is_empty() {
            issues.push(ValidationIssue::error(
                path,
                "must include at least one item",
            ));
        }
    }
    if !(1..=3).contains(&session.foundation.weakest_assumptions.len()) {
        issues.push(ValidationIssue::error(
            "foundation.weakest_assumptions",
            "must include 1-3 items",
        ));
    }
    if !(1..=2).contains(&session.foundation.invalidation_conditions.len()) {
        issues.push(ValidationIssue::error(
            "foundation.invalidation_conditions",
            "must include 1-2 items",
        ));
    }
    if session.foundation.key_vulnerability.trim().is_empty() {
        issues.push(ValidationIssue::error(
            "foundation.key_vulnerability",
            "must be a non-empty string",
        ));
    }
    if session.diagnostics.is_empty() {
        issues.push(ValidationIssue::error(
            "diagnostics",
            "must include at least one cross-harness diagnostic",
        ));
    }
    for (idx, diagnostic) in session.diagnostics.iter().enumerate() {
        if diagnostic.item.trim().is_empty() {
            issues.push(ValidationIssue::error(
                format!("diagnostics[{idx}].item"),
                "must be a non-empty string",
            ));
        }
        if diagnostic.diagnosis.trim().is_empty() {
            issues.push(ValidationIssue::error(
                format!("diagnostics[{idx}].diagnosis"),
                "must be a non-empty string",
            ));
        }
    }

    ValidationResult { issues }
}

pub fn build_origin_packet(session: &SessionConfig, payload_id: &str) -> String {
    let envelope = PayloadEnvelope {
        route: "RX".to_string(),
        payload_id: payload_id.to_string(),
        body: [
            format!("From: {}", session.origin.name),
            format!("To: {}", session.partner.name),
            "Subject: Cross-Harness Scaffolder - Phase 0 Round 0".to_string(),
            "STYLE_GUIDE:\n- Tone: Calm, spec-like.\n- ASCII only.".to_string(),
            render_dossier(&session.dossier),
            render_foundation(&session.foundation),
            render_diagnostics(&session.diagnostics),
            "SHAPE_LOCK:\n- Return payload markers and PAYLOAD_ECHO.\n- Pick one winner; no ties."
                .to_string(),
        ]
        .join("\n\n"),
    };

    [
        "1. CORE_PROBLEM_STATEMENT".to_string(),
        session.dossier.core_problem.clone(),
        String::new(),
        "2. PARTNER_HARNESS_PACKET".to_string(),
        "```".to_string(),
        envelope.render(),
        "```".to_string(),
        String::new(),
        "3. TRANSMISSION_CHECKLIST".to_string(),
        "[ ] R0 Gate passed".to_string(),
        "[ ] Foundation >=70% (Phase 0)".to_string(),
        "[ ] Dossier updated".to_string(),
        "[ ] Structural vulnerabilities carried".to_string(),
        "VERDICT: ITERATE (Phase 0 Round 0 of 5)".to_string(),
    ]
    .join("\n")
}

pub fn validate_payload_envelope(text: &str) -> bool {
    let mut lines = text.lines();
    let Some(first) = lines.next() else {
        return false;
    };
    let Some(last) = text.lines().last() else {
        return false;
    };
    let begin = parse_marker(first, "BEGIN_PAYLOAD");
    let end = parse_marker(last, "END_PAYLOAD");
    begin.is_some() && begin == end
}

pub fn compact_session_state(session: &SessionConfig, origin_packet: &str) -> CompactSessionState {
    let mut canonical_protocol = BTreeMap::new();
    canonical_protocol.insert("name".to_string(), CANONICAL_PROTOCOL_NAME.to_string());
    canonical_protocol.insert("url".to_string(), CANONICAL_PROTOCOL_URL.to_string());

    let mut token_budget = BTreeMap::new();
    token_budget.insert(
        "origin_packet_estimate".to_string(),
        estimate_tokens(origin_packet),
    );
    token_budget.insert("recommended_hot_state_budget".to_string(), 900);

    CompactSessionState {
        protocol_version: PROTOCOL_VERSION.to_string(),
        canonical_protocol,
        title: session.title.clone(),
        status: "EXPLORING".to_string(),
        participant_count: session.participant_count(),
        dossier_hash: content_hash(&render_dossier(&session.dossier)),
        diagnostics: session
            .diagnostics
            .iter()
            .map(|diagnostic| diagnostic.item.clone())
            .collect(),
        token_budget,
    }
}

pub fn run_consensus_report(session: &SessionConfig, payload_id: &str) -> ConsensusReport {
    let validation = validate_session_config(session);
    let mut findings = Vec::new();
    for issue in &validation.issues {
        findings.push(ConsensusFinding {
            check: issue.path.clone(),
            status: if issue.severity == IssueSeverity::Critical {
                "FAIL".to_string()
            } else {
                "WARN".to_string()
            },
            detail: issue.message.clone(),
            severity: issue.severity.clone(),
        });
    }
    if validation.ok() {
        findings.push(ConsensusFinding {
            check: "config".to_string(),
            status: "PASS".to_string(),
            detail: "session config is valid".to_string(),
            severity: IssueSeverity::Info,
        });
    }

    let packet = build_origin_packet(session, payload_id);
    let payload = extract_code_block(&packet).unwrap_or_default();
    findings.push(ConsensusFinding {
        check: "payload envelope".to_string(),
        status: if validate_payload_envelope(payload) {
            "PASS".to_string()
        } else {
            "FAIL".to_string()
        },
        detail: "origin packet uses matching payload markers".to_string(),
        severity: if validate_payload_envelope(payload) {
            IssueSeverity::Info
        } else {
            IssueSeverity::Critical
        },
    });
    findings.push(ConsensusFinding {
        check: "ascii packet".to_string(),
        status: if packet.is_ascii() {
            "PASS".to_string()
        } else {
            "FAIL".to_string()
        },
        detail: "origin packet is ASCII".to_string(),
        severity: if packet.is_ascii() {
            IssueSeverity::Info
        } else {
            IssueSeverity::Critical
        },
    });

    let critical = findings
        .iter()
        .filter(|finding| finding.status == "FAIL" && finding.severity == IssueSeverity::Critical)
        .count();
    let warnings = findings
        .iter()
        .filter(|finding| finding.status == "WARN")
        .count();
    let penalty = 15 * critical + 5 * warnings;
    ConsensusReport {
        verdict: if critical == 0 {
            Verdict::Pass
        } else {
            Verdict::Fail
        },
        score: 100usize.saturating_sub(penalty).min(100) as u8,
        findings,
    }
}

pub fn build_artifact_manifest(
    artifacts: Vec<ArtifactEntry>,
    signer: &str,
    created_at: Option<&str>,
) -> BundleManifest {
    let mut artifacts = artifacts;
    artifacts.sort_by(|left, right| left.path.cmp(&right.path));
    BundleManifest {
        manifest_version: MANIFEST_VERSION.to_string(),
        created_at: created_at.map_or_else(now_utc, ToOwned::to_owned),
        signer: signer.to_string(),
        artifact_count: artifacts.len(),
        total_token_estimate: artifacts
            .iter()
            .map(|artifact| artifact.token_estimate)
            .sum(),
        artifacts,
        signature: None,
    }
}

pub fn build_directory_manifest(
    root: impl AsRef<Path>,
    signer: &str,
) -> Result<BundleManifest, ChsError> {
    let root = root.as_ref();
    let mut files = Vec::new();
    collect_files(root, root, &mut files)?;
    let artifacts = files
        .into_iter()
        .filter(|path| {
            path.file_name()
                .and_then(|name| name.to_str())
                .is_none_or(|name| name != "bundle_manifest.json")
        })
        .map(|path| artifact_entry_from_file(root, &path))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(build_artifact_manifest(artifacts, signer, None))
}

pub fn sign_manifest_hmac(
    manifest: &BundleManifest,
    secret: &str,
    key_id: &str,
) -> Result<BundleManifest, ChsError> {
    if secret.is_empty() {
        return Err(ChsError::MissingSigningSecret);
    }
    let mut signed = manifest.clone();
    signed.signature = None;
    let canonical = canonical_json(&signed)?;
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes())
        .map_err(|_| ChsError::MissingSigningSecret)?;
    mac.update(canonical.as_bytes());
    let value = hex::encode(mac.finalize().into_bytes());
    signed.signature = Some(ManifestSignature {
        algorithm: "hmac_sha256".to_string(),
        key_id: key_id.to_string(),
        value,
    });
    Ok(signed)
}

pub fn verify_manifest_hmac(manifest: &BundleManifest, secret: &str) -> Result<bool, ChsError> {
    let Some(signature) = &manifest.signature else {
        return Ok(false);
    };
    if signature.algorithm != "hmac_sha256" {
        return Ok(false);
    }
    let expected = sign_manifest_hmac(manifest, secret, &signature.key_id)?;
    Ok(expected
        .signature
        .is_some_and(|expected| constant_time_eq(&expected.value, &signature.value)))
}

pub fn build_transparency_log_entry(
    manifest: &BundleManifest,
    log_id: &str,
    source: &str,
    previous_entry_hash: Option<&str>,
) -> Result<TransparencyLogEntry, ChsError> {
    let manifest_hash = content_hash(&canonical_json(manifest)?);
    let signature = manifest.signature.clone().unwrap_or(ManifestSignature {
        algorithm: String::new(),
        key_id: String::new(),
        value: String::new(),
    });
    let mut entry = TransparencyLogEntry {
        log_version: TRANSPARENCY_LOG_VERSION.to_string(),
        log_id: log_id.to_string(),
        recorded_at: now_utc(),
        source: source.to_string(),
        manifest_hash,
        manifest_version: manifest.manifest_version.clone(),
        manifest_created_at: manifest.created_at.clone(),
        signer: manifest.signer.clone(),
        artifact_count: manifest.artifact_count,
        signature_algorithm: signature.algorithm,
        signature_key_id: signature.key_id,
        signature_value: signature.value,
        previous_entry_hash: previous_entry_hash.unwrap_or_default().to_string(),
        entry_hash: String::new(),
    };
    entry.entry_hash = content_hash(&canonical_json(&entry)?);
    Ok(entry)
}

pub fn session_config_schema() -> Value {
    json!({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "CrossHarnessSessionConfig",
        "type": "object",
        "required": ["title", "origin", "partner", "dossier", "foundation", "diagnostics"],
        "properties": {
            "title": {"type": "string"},
            "human_bridge": {"type": "string"},
            "origin": {"$ref": "#/$defs/profile"},
            "partner": {"$ref": "#/$defs/profile"},
            "validators": {"type": "array", "items": {"$ref": "#/$defs/profile"}},
            "dossier": {"type": "object"},
            "foundation": {"type": "object"},
            "diagnostics": {"type": "array"}
        },
        "$defs": {
            "profile": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "model": {"type": "string"},
                    "role": {"type": "string"}
                }
            }
        }
    })
}

pub fn content_hash(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    hex::encode(hasher.finalize())
}

pub fn estimate_tokens(content: &str) -> usize {
    let words = content.split_whitespace().count();
    words.max((content.len() / 4).max(1))
}

pub fn ascii_only(content: &str) -> String {
    content
        .chars()
        .map(|character| if character.is_ascii() { character } else { '?' })
        .collect()
}

fn validate_profile(
    path: impl Into<String>,
    profile: &HarnessRef,
    issues: &mut Vec<ValidationIssue>,
) {
    let path = path.into();
    if profile.name.trim().is_empty() {
        issues.push(ValidationIssue::error(
            format!("{path}.name"),
            "must be a non-empty string",
        ));
    }
}

fn render_dossier(dossier: &DossierConfig) -> String {
    [
        "DOSSIER:".to_string(),
        format!("CORE PROBLEM: {}", dossier.core_problem),
        format!("GOAL STATE: {:?}", dossier.goal_state),
        format!("CURRENT STATE: {:?}", dossier.current_state),
        format!("CONSTRAINTS: {:?}", dossier.constraints),
        format!("SCOPE: {:?}", dossier.scope),
        format!("ORIGIN DIRECTION: {:?}", dossier.origin_direction),
    ]
    .join("\n")
}

fn render_foundation(foundation: &FoundationConfig) -> String {
    [
        "FOUNDATION_DISCLOSURE:".to_string(),
        format!("WEAKEST_ASSUMPTIONS: {:?}", foundation.weakest_assumptions),
        format!(
            "WHAT_COULD_INVALIDATE: {:?}",
            foundation.invalidation_conditions
        ),
        format!("KEY_VULNERABILITY: {}", foundation.key_vulnerability),
    ]
    .join("\n")
}

fn render_diagnostics(diagnostics: &[DiagnosticConfig]) -> String {
    let mut lines = vec!["CROSS_HARNESS_DIAGNOSTICS:".to_string()];
    for diagnostic in diagnostics {
        lines.push(format!(
            "- {}: observed={}; constraint={}; diagnosis={}",
            diagnostic.item,
            diagnostic.observed_layer.as_str(),
            diagnostic.constraint_layer.as_str(),
            diagnostic.diagnosis
        ));
    }
    lines.join("\n")
}

fn extract_code_block(packet: &str) -> Option<&str> {
    let start = packet.find("```")?;
    let after_start = &packet[start + 3..];
    let end = after_start.find("```")?;
    Some(after_start[..end].trim())
}

fn parse_marker(line: &str, prefix: &str) -> Option<(String, String)> {
    let line = line.trim();
    let remainder = line.strip_prefix(prefix)?.trim();
    let parts: Vec<&str> = remainder.split_whitespace().collect();
    if parts.len() != 2 {
        return None;
    }
    let route = parts[0].strip_prefix('[')?.strip_suffix(']')?;
    let id = parts[1].strip_prefix('[')?.strip_suffix(']')?;
    if route.is_empty() || id.len() != 6 || !id.chars().all(|c| c.is_ascii_alphanumeric()) {
        return None;
    }
    Some((route.to_string(), id.to_string()))
}

fn normalized(value: &str) -> String {
    value
        .trim()
        .to_ascii_lowercase()
        .replace(['_', '-', ' '], "")
}

fn collect_files(root: &Path, current: &Path, files: &mut Vec<PathBuf>) -> Result<(), ChsError> {
    for entry in fs::read_dir(current)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            collect_files(root, &path, files)?;
        } else if path.is_file() {
            let canonical = path.canonicalize()?;
            if canonical.starts_with(root.canonicalize()?) {
                files.push(path);
            }
        }
    }
    Ok(())
}

fn artifact_entry_from_file(root: &Path, path: &Path) -> Result<ArtifactEntry, ChsError> {
    let data = fs::read(path)?;
    let rel = path
        .strip_prefix(root)
        .unwrap_or(path)
        .to_string_lossy()
        .replace('\\', "/");
    let content_hash = hex::encode(Sha256::digest(&data));
    let content = String::from_utf8_lossy(&data);
    Ok(ArtifactEntry {
        path: rel,
        purpose: "bundle file".to_string(),
        content_hash,
        token_estimate: estimate_tokens(&content),
    })
}

fn canonical_json<T: Serialize>(value: &T) -> Result<String, ChsError> {
    let value = serde_json::to_value(value)?;
    Ok(canonical_value(&value))
}

fn canonical_value(value: &Value) -> String {
    match value {
        Value::Null => "null".to_string(),
        Value::Bool(item) => item.to_string(),
        Value::Number(item) => item.to_string(),
        Value::String(item) => serde_json::to_string(item).expect("string serialization"),
        Value::Array(items) => {
            let body = items
                .iter()
                .map(canonical_value)
                .collect::<Vec<_>>()
                .join(",");
            format!("[{body}]")
        }
        Value::Object(items) => {
            let body = items
                .iter()
                .filter(|(key, value)| *key != "signature" && !value.is_null())
                .map(|(key, value)| {
                    format!(
                        "{}:{}",
                        serde_json::to_string(key).expect("key serialization"),
                        canonical_value(value)
                    )
                })
                .collect::<Vec<_>>()
                .join(",");
            format!("{{{body}}}")
        }
    }
}

fn constant_time_eq(left: &str, right: &str) -> bool {
    if left.len() != right.len() {
        return false;
    }
    left.bytes()
        .zip(right.bytes())
        .fold(0u8, |acc, (a, b)| acc | (a ^ b))
        == 0
}

fn now_utc() -> String {
    Utc::now().to_rfc3339_opts(SecondsFormat::Secs, true)
}

#[allow(dead_code)]
fn unique_harness_names(session: &SessionConfig) -> BTreeSet<String> {
    let mut names = BTreeSet::new();
    names.insert(normalized(&session.origin.name));
    names.insert(normalized(&session.partner.name));
    for validator in &session.validators {
        names.insert(normalized(&validator.name));
    }
    names
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_session() -> SessionConfig {
        serde_yaml::from_str(include_str!("../../../examples/database_design.yaml")).unwrap()
    }

    #[test]
    fn validates_example_config() {
        let session = sample_session();
        let result = validate_session_config(&session);
        assert!(result.ok(), "{:?}", result.issues);
    }

    #[test]
    fn catches_missing_diagnostics() {
        let mut session = sample_session();
        session.diagnostics.clear();
        let result = validate_session_config(&session);
        assert!(!result.ok());
        assert!(result
            .issues
            .iter()
            .any(|issue| issue.path == "diagnostics"));
    }

    #[test]
    fn builds_valid_payload_envelope() {
        let session = sample_session();
        let packet = build_origin_packet(&session, "ABC123");
        let payload = extract_code_block(&packet).unwrap();
        assert!(validate_payload_envelope(payload));
        assert!(packet.is_ascii());
    }

    #[test]
    fn consensus_report_passes_example() {
        let report = run_consensus_report(&sample_session(), "CI0001");
        assert!(report.passed(), "{}", report.render_markdown());
        assert!(report.score >= 90);
    }

    #[test]
    fn signs_and_verifies_hmac_manifest() {
        let artifacts = vec![ArtifactEntry {
            path: "cross-harness/session_state.json".to_string(),
            purpose: "compact state".to_string(),
            content_hash: content_hash("{}"),
            token_estimate: 1,
        }];
        let manifest = build_artifact_manifest(artifacts, "test", Some("2026-01-01T00:00:00Z"));
        let signed = sign_manifest_hmac(&manifest, "secret", "local").unwrap();
        assert!(verify_manifest_hmac(&signed, "secret").unwrap());
        assert!(!verify_manifest_hmac(&signed, "wrong").unwrap());
    }

    #[test]
    fn transparency_log_entry_hashes_manifest() {
        let manifest = build_artifact_manifest(Vec::new(), "test", Some("2026-01-01T00:00:00Z"));
        let signed = sign_manifest_hmac(&manifest, "secret", "local").unwrap();
        let entry =
            build_transparency_log_entry(&signed, "local", "bundle_manifest.json", None).unwrap();
        assert_eq!(entry.log_version, TRANSPARENCY_LOG_VERSION);
        assert_eq!(entry.entry_hash.len(), 64);
    }

    #[test]
    fn compact_state_uses_hashes_not_full_packets() {
        let session = sample_session();
        let packet = build_origin_packet(&session, "ABC123");
        let state = compact_session_state(&session, &packet);
        assert_eq!(state.dossier_hash.len(), 64);
        assert!(!serde_json::to_string(&state)
            .unwrap()
            .contains("BEGIN_PAYLOAD"));
    }
}
