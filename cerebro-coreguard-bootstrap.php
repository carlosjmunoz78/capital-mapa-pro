<?php
/**
 * Plugin Name: CEREBRO Core Guard Bootstrap
 * Description: Temporary PRE-PROD-only bootstrap to deploy the hash-verified Core Guard Backup & Recovery Gate build.
 * Version: 0.1.0
 * Author: Fénix Capital
 */
defined('ABSPATH') || exit;

function fenix_cerebro_bootstrap_coreguard_run(): void {
    $host = strtolower((string) wp_parse_url(home_url('/'), PHP_URL_HOST));
    if ($host !== 'staging.fenixcapital.es') {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'wrong_host','host'=>$host,'at'=>gmdate('c')], false);
        return;
    }
    if (!class_exists('ZipArchive')) {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'ziparchive_missing','at'=>gmdate('c')], false);
        return;
    }

    $artifact = WP_CONTENT_DIR . '/uploads/2026/09/fenix-core-guard-1.0.0-rc9-direct-deploy.zip';
    $expected = '8faa92b15e65761e67c9141a8a57bd8b56ef6ad4ed31fb786e42f19d1d4fe6e8';
    if (!is_readable($artifact)) {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'artifact_missing','at'=>gmdate('c')], false);
        return;
    }
    $actual = hash_file('sha256', $artifact);
    if (!is_string($actual) || !hash_equals($expected, $actual)) {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'artifact_hash_mismatch','actual'=>$actual,'at'=>gmdate('c')], false);
        return;
    }

    $current = WP_PLUGIN_DIR . '/fenix-core-guard';
    if (!is_dir($current) || !is_readable($current . '/fenix-core-guard.php')) {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'current_coreguard_missing','at'=>gmdate('c')], false);
        return;
    }

    $backup_root = WP_CONTENT_DIR . '/fenix-core-guard-bootstrap-backup';
    if (!wp_mkdir_p($backup_root)) {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'backup_dir_failed','at'=>gmdate('c')], false);
        return;
    }
    $backup = trailingslashit($backup_root) . 'coreguard-pre-backup-gate-' . gmdate('Ymd-His') . '.zip';
    $zip = new ZipArchive();
    if ($zip->open($backup, ZipArchive::CREATE | ZipArchive::OVERWRITE) !== true) {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'backup_open_failed','at'=>gmdate('c')], false);
        return;
    }
    try {
        $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($current, FilesystemIterator::SKIP_DOTS));
        foreach ($it as $file) {
            if (!$file->isFile()) continue;
            $absolute = $file->getPathname();
            $relative = 'fenix-core-guard/' . ltrim(str_replace('\\', '/', substr($absolute, strlen($current))), '/');
            if (!$zip->addFile($absolute, $relative)) {
                $zip->close();
                @unlink($backup);
                update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'backup_add_failed','at'=>gmdate('c')], false);
                return;
            }
        }
    } catch (Throwable $e) {
        $zip->close();
        @unlink($backup);
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'backup_exception','at'=>gmdate('c')], false);
        return;
    }
    $zip->close();
    if (!is_readable($backup) || filesize($backup) < 1000) {
        @unlink($backup);
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'backup_invalid','at'=>gmdate('c')], false);
        return;
    }
    $backup_hash = hash_file('sha256', $backup);

    require_once ABSPATH . 'wp-admin/includes/file.php';
    WP_Filesystem();
    $result = unzip_file($artifact, WP_PLUGIN_DIR);
    if (is_wp_error($result)) {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'deploy_unzip_failed','error'=>$result->get_error_code(),'backup'=>$backup,'backup_sha256'=>$backup_hash,'at'=>gmdate('c')], false);
        return;
    }
    if (!is_readable($current . '/fenix-core-guard-backup-recovery.php')) {
        update_option('fenix_cerebro_bootstrap_coreguard_result_v1', ['ok'=>false,'code'=>'backup_recovery_module_missing_after_deploy','backup'=>$backup,'backup_sha256'=>$backup_hash,'at'=>gmdate('c')], false);
        return;
    }

    update_option('fenix_cerebro_bootstrap_coreguard_result_v1', [
        'ok'=>true,
        'code'=>'deployed',
        'artifact_sha256'=>$actual,
        'backup'=>$backup,
        'backup_sha256'=>$backup_hash,
        'module'=>basename($current . '/fenix-core-guard-backup-recovery.php'),
        'at'=>gmdate('c'),
    ], false);
}

register_activation_hook(__FILE__, 'fenix_cerebro_bootstrap_coreguard_run');
