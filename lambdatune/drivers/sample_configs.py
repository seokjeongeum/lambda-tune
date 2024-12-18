MY_SQL = [
    "SET GLOBAL max_connections = 40;",
    "SET GLOBAL innodb_buffer_pool_size = 12*1024*1024*1024;",
    "SET GLOBAL query_cache_size = 12*1024*1024*1024;",
    "SET GLOBAL innodb_buffer_pool_instances = 2*1024*1024*1024;",
    "SET GLOBAL innodb_log_file_size = 16*1024*1024;",
    "SET GLOBAL innodb_stats_sample_pages = 500;",
    "SET GLOBAL innodb_random_read_ahead = 1;",
    "SET GLOBAL sort_buffer_size = 26214*1024;",
    "SET GLOBAL large_pages = 'OFF';",
    "SET GLOBAL innodb_log_buffer_size = 4*1024*1024*1024;",
    "SET GLOBAL innodb_log_files_in_group = 16;",
    "SET GLOBAL thread_concurrency = 4;",
    "SET GLOBAL innodb_thread_concurrency = 2;",
    "SET GLOBAL innodb_read_io_threads = 4;",
    "SET GLOBAL innodb_write_io_threads = 2;"
]

POSTGRES = [
    "ALTER SYSTEM SET max_connections = 40;",
    "ALTER SYSTEM SET shared_buffers = '12GB';",
    "ALTER SYSTEM SET effective_cache_size = '12GB';",
    "ALTER SYSTEM SET maintenance_work_mem = '2GB';",
    "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
    "ALTER SYSTEM SET wal_buffers = '16MB';",
    "ALTER SYSTEM SET default_statistics_target = 500;",
    "ALTER SYSTEM SET random_page_cost = 1.1;",
    "ALTER SYSTEM SET work_mem = '26214kB';",
    "ALTER SYSTEM SET huge_pages = 'off';",
    "ALTER SYSTEM SET min_wal_size = '4GB';",
    "ALTER SYSTEM SET max_wal_size = '16GB';",
    "ALTER SYSTEM SET max_worker_processes = 4;",
    "ALTER SYSTEM SET max_parallel_workers_per_gather = 2;",
    "ALTER SYSTEM SET max_parallel_workers = 4;",
    "ALTER SYSTEM SET max_parallel_maintenance_workers = 2;"
]