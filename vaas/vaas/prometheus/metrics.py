from prometheus_client import Counter, Gauge, Summary

# Counters
events_with_change = Counter('events_with_change', 'Description of counter')
events_without_change = Counter('events_without_change', 'Description of counter')

# Gauges
varnish_cluster_successful_reload_vcl = Gauge('successful_reload_vcl', 'Description of counter')

# Summaries
s_processing_vcl_task_with_change = Summary('s_processing_vcl_task_with_change_seconds', '')
s_processing_vcl_task_without_change = Summary('s_processing_vcl_task_without_change_seconds', '')
s_queue_time_from_order_to_execute_task = Summary('s_queue_time_from_order_to_execute_task_seconds', '')
s_render_vcl_for_servers = Summary('s_render_vcl_for_servers_seconds', '')
s_fetch_render_data = Summary('s_fetch_render_data_seconds', '')
s_extract_servers_by_clusters = Summary('s_extract_servers_by_clusters_seconds', '')
s_use_vcl_list = Summary('s_use_vcl_list_seconds', '')
s__discard_unused_vcls = Summary('s_discard_unused_vcls_seconds', '')
s__append_vcl = Summary('s_append_vcl_seconds', '')
s_load_vcl_list = Summary('s_load_vcl_list_seconds', '')
s__format_vcl_list = Summary('s_format_vcl_list_seconds', '')
s__handle_load_error = Summary('s_handle_load_error_seconds', '')
s__update_vcl_versions = Summary('s_update_vcl_versions_seconds', '')
s_expand = Summary('s_expand_seconds', '')
s__get_template = Summary('s_get_template_seconds', '')
s__render = Summary('s_render_seconds', '')
s_get_db_tag_content = Summary('s_get_db_tag_content_seconds', '')
s_prepare_redirects = Summary('s_prepare_redirects_seconds', '')
s_prepare_route = Summary('s_prepare_route_seconds', '')
s_prepare_cluster_directors = Summary('s_prepare_cluster_directors_seconds', '')
s_prepare_vcl_directors = Summary('s_prepare_vcl_directors_seconds', '')
s_prepare_probe = Summary('s_prepare_probe_seconds', '')
s_get_expanded_tags = Summary('s_get_expanded_tags_seconds', '')
s_distribute_backends = Summary('s_distribute_backends_seconds', '')
s_prepare_canary_backends = Summary('s_prepare_canary_backends_seconds', '')
s_prepare_backend_dictionary = Summary('s_prepare_backend_dictionary_seconds', '')
s_purge_url = Summary('s_purge_url_seconds', '')