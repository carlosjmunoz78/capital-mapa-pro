<?php
// PHP test of copied LAB candidate only; never loads WordPress production.
define('ABSPATH', __DIR__);
function add_action(...$args) { return true; }
function add_filter(...$args) { return true; }
require __DIR__ . '/../fenix-cerebro-leads-candidate.php';
function ok($v,$expected,$label) {
    if ($v !== $expected) { fwrite(STDERR, "FAIL $label\n"); exit(1); }
}
foreach ([false,null,0,"", "false","0","off","no","FALSE","FALSE ",[], "null"] as $value) {
    ok(fenix_cerebro_marketing_flag($value),false,"reject unapproved marketing");
}
foreach ([true,1,"true","TRUE","1","on","yes","si","sí","SÍ"] as $value) {
    ok(fenix_cerebro_marketing_flag($value),true,"accept explicit positive marketing");
}
ok(fenix_cerebro_elementor_marketing_flag([["title"=>"Aviso de privacidad","value"=>"on"]]),false,"privacy is not marketing");
ok(fenix_cerebro_elementor_marketing_flag([["title"=>"Newsletter","value"=>"on"]]),true,"explicit newsletter accepted");
ok(fenix_cerebro_elementor_marketing_flag([["title"=>"Boletín","value"=>"false"]]),false,"string false rejected");
ok(fenix_cerebro_elementor_marketing_flag([["title"=>"BOLETÍN","value"=>"on"]]),true,"uppercase unicode newsletter label accepted");
ok(fenix_cerebro_elementor_marketing_flag([["title"=>"Comunicaciones comerciales","value"=>"1"]]),true,"explicit commercial");
ok(fenix_cerebro_elementor_marketing_flag([["title"=>"Aceptación RGPD","value"=>"on"]]),false,"rgpd not marketing");
ok(fenix_cerebro_elementor_marketing_flag([["title"=>"Newsletter","value"=>false]]),false,"unchecked newsletter");
$source=file_get_contents(__DIR__.'/../fenix-cerebro-leads-candidate.php');
ok(str_contains($source,"consent_marketing:marketingOptin(form)"),true,"browser payload captures checkbox");
ok(substr_count($source,"consent_marketing:marketingOptin(form)"),2,"both native flows capture") ;
ok(str_contains($source,'name="newsletter" value="on"'),true,"explicit optional field exists");
ok(str_contains($source,"'consent_marketing' => fenix_cerebro_marketing_flag("),true,"strict parser");
ok(str_contains($source,"'consent_marketing' => fenix_cerebro_elementor_marketing_flag("),true,"elementor mapping");
echo "NEWS001 PHP marketing consent strict LAB tests: PASS\n";