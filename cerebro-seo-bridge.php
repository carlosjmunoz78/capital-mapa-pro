<?php
/**
 * Plugin Name: CEREBRO SEO Bridge
 * Description: Puente REST seguro para lectura y escritura SEO de Fénix Capital por CEREBRO.
 * Version: 1.0.0
 * Author: Fénix Capital
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

final class Fenix_Cerebro_SEO_Bridge {
    const NS = 'cerebro/v1';

    public static function init() {
        add_action( 'rest_api_init', array( __CLASS__, 'register_routes' ) );
    }

    public static function register_routes() {
        register_rest_route(
            self::NS,
            '/seo/(?P<id>\\d+)',
            array(
                array(
                    'methods'             => WP_REST_Server::READABLE,
                    'permission_callback' => array( __CLASS__, 'can_edit' ),
                    'callback'            => array( __CLASS__, 'read_seo' ),
                    'args'                => array(
                        'id' => array(
                            'validate_callback' => function ( $value ) {
                                return absint( $value ) > 0;
                            },
                        ),
                    ),
                ),
                array(
                    'methods'             => array( 'POST', 'PUT', 'PATCH' ),
                    'permission_callback' => array( __CLASS__, 'can_edit' ),
                    'callback'            => array( __CLASS__, 'write_seo' ),
                    'args'                => array(
                        'id' => array(
                            'validate_callback' => function ( $value ) {
                                return absint( $value ) > 0;
                            },
                        ),
                    ),
                ),
            )
        );

        register_rest_route(
            self::NS,
            '/health',
            array(
                'methods'             => WP_REST_Server::READABLE,
                'permission_callback' => function () {
                    return current_user_can( 'edit_posts' );
                },
                'callback'            => function () {
                    return rest_ensure_response(
                        array(
                            'ok'      => true,
                            'bridge'  => 'cerebro-seo-bridge',
                            'version' => '1.0.0',
                            'yoast'   => defined( 'WPSEO_VERSION' ),
                        )
                    );
                },
            )
        );
    }

    public static function can_edit( WP_REST_Request $request ) {
        $id = absint( $request['id'] );
        return $id && current_user_can( 'edit_post', $id );
    }

    private static function get_post_or_error( $id ) {
        $post = get_post( $id );
        if ( ! $post ) {
            return new WP_Error(
                'cerebro_seo_not_found',
                'Contenido no encontrado.',
                array( 'status' => 404 )
            );
        }
        return $post;
    }

    private static function payload( $id, $post ) {
        return array(
            'ok'        => true,
            'bridge'    => 'cerebro-seo-bridge',
            'version'   => '1.0.0',
            'id'        => $id,
            'post_type' => $post->post_type,
            'status'    => $post->post_status,
            'permalink' => get_permalink( $id ),
            'seo'       => array(
                'title'           => (string) get_post_meta( $id, '_yoast_wpseo_title', true ),
                'description'     => (string) get_post_meta( $id, '_yoast_wpseo_metadesc', true ),
                'canonical'       => (string) get_post_meta( $id, '_yoast_wpseo_canonical', true ),
                'focus_keyphrase' => (string) get_post_meta( $id, '_yoast_wpseo_focuskw', true ),
                'noindex'         => get_post_meta( $id, '_yoast_wpseo_meta-robots-noindex', true ) === '1',
                'nofollow'        => get_post_meta( $id, '_yoast_wpseo_meta-robots-nofollow', true ) === '1',
            ),
        );
    }

    public static function read_seo( WP_REST_Request $request ) {
        $id   = absint( $request['id'] );
        $post = self::get_post_or_error( $id );
        if ( is_wp_error( $post ) ) {
            return $post;
        }
        return rest_ensure_response( self::payload( $id, $post ) );
    }

    public static function write_seo( WP_REST_Request $request ) {
        $id   = absint( $request['id'] );
        $post = self::get_post_or_error( $id );
        if ( is_wp_error( $post ) ) {
            return $post;
        }

        $params = $request->get_json_params();
        if ( ! is_array( $params ) ) {
            $params = $request->get_params();
        }

        $map = array(
            'title'             => '_yoast_wpseo_title',
            'meta_title'        => '_yoast_wpseo_title',
            'description'       => '_yoast_wpseo_metadesc',
            'metadesc'          => '_yoast_wpseo_metadesc',
            'meta_description'  => '_yoast_wpseo_metadesc',
            'canonical'         => '_yoast_wpseo_canonical',
            'focuskw'           => '_yoast_wpseo_focuskw',
            'focus_keyword'     => '_yoast_wpseo_focuskw',
            'focus_keyphrase'   => '_yoast_wpseo_focuskw',
        );

        $updated = array();

        foreach ( $map as $input_key => $meta_key ) {
            if ( ! array_key_exists( $input_key, $params ) ) {
                continue;
            }

            $raw = (string) $params[ $input_key ];
            if ( 'canonical' === $input_key ) {
                $value = esc_url_raw( $raw );
            } else {
                $value = sanitize_text_field( $raw );
            }

            if ( '' === $value ) {
                delete_post_meta( $id, $meta_key );
            } else {
                update_post_meta( $id, $meta_key, $value );
            }
            $updated[ $input_key ] = $value;
        }

        foreach (
            array(
                'noindex'  => '_yoast_wpseo_meta-robots-noindex',
                'nofollow' => '_yoast_wpseo_meta-robots-nofollow',
            ) as $input_key => $meta_key
        ) {
            if ( ! array_key_exists( $input_key, $params ) ) {
                continue;
            }

            $bool = filter_var( $params[ $input_key ], FILTER_VALIDATE_BOOLEAN, FILTER_NULL_ON_FAILURE );
            if ( null === $bool ) {
                return new WP_Error(
                    'cerebro_seo_invalid_boolean',
                    'Valor booleano no válido para ' . $input_key . '.',
                    array( 'status' => 400 )
                );
            }

            if ( $bool ) {
                update_post_meta( $id, $meta_key, '1' );
            } else {
                delete_post_meta( $id, $meta_key );
            }
            $updated[ $input_key ] = $bool;
        }

        if ( ! empty( $updated ) ) {
            wp_update_post( array( 'ID' => $id ) );
            clean_post_cache( $id );

            if ( function_exists( 'YoastSEO' ) ) {
                try {
                    YoastSEO()->helpers->indexable->reset_permalink( $id );
                } catch ( Throwable $e ) {
                    // El bridge sigue siendo válido aunque Yoast no exponga esta ayuda en una versión concreta.
                }
            }
        }

        $response            = self::payload( $id, get_post( $id ) );
        $response['updated'] = $updated;
        return rest_ensure_response( $response );
    }
}

Fenix_Cerebro_SEO_Bridge::init();
