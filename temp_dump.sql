
    -- Output schema recreation commands
    SELECT E'-- Schema Recreation\n';
    SELECT 'CREATE SCHEMA IF NOT EXISTS public;';
    
    -- Drop existing tables
    SELECT E'\n-- Drop existing tables\n';
    SELECT string_agg(
        'DROP TABLE IF EXISTS ' || quote_ident(tablename) || ' CASCADE;',
        E'\n'
    )
    FROM pg_tables 
    WHERE schemaname = 'public';
    
    -- Create tables
    SELECT E'\n-- Create tables\n';
    SELECT string_agg(
        pg_get_tabledef::text || ';',
        E'\n\n'
    )
    FROM (
        SELECT format(
            'CREATE TABLE %I.%I (%s)',
            schemaname,
            tablename,
            string_agg(
                format(
                    '%I %s%s',
                    attname,
                    format_type(atttypid, atttypmod),
                    CASE 
                        WHEN attnotnull THEN ' NOT NULL'
                        ELSE ''
                    END
                ),
                ', '
            )
        ) as pg_get_tabledef
        FROM pg_tables t
        JOIN pg_class c ON c.relname = t.tablename
        JOIN pg_namespace n ON n.nspname = t.schemaname AND n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE t.schemaname = 'public'
        AND a.attnum > 0
        AND NOT a.attisdropped
        GROUP BY t.schemaname, t.tablename
    ) table_defs;

    -- Create functions
    SELECT E'\n-- Create functions\n';
    SELECT string_agg(
        pg_get_functiondef(p.oid),
        E'\n\n'
    )
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public';

    -- Table Data
    SELECT E'\n-- Table Data\n';
    WITH table_data AS (
        SELECT 
            t.tablename,
            format(
                E'\n-- Data for table %I\nCOPY %I (%s) FROM stdin;\n%s\n\.',
                t.tablename,
                t.tablename,
                (
                    SELECT string_agg(quote_ident(attname), ', ')
                    FROM pg_attribute a
                    WHERE a.attrelid = format('%I.%I', t.schemaname, t.tablename)::regclass
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                ),
                (
                    SELECT coalesce(
                        string_agg(
                            CASE 
                                WHEN row_to_json(r)::text = 'null' THEN '\N'
                                ELSE array_to_string(
                                    ARRAY(
                                        SELECT replace(
                                            replace(
                                                col::text,
                                                E'\',
                                                E'\\'
                                            ),
                                            E'\n',
                                            E'\\n'
                                        )
                                        FROM json_each_text(row_to_json(r)) col
                                    ),
                                    E'\t'
                                )
                            END,
                            E'\n'
                        ),
                        ''
                    )
                    FROM (
                        SELECT *
                        FROM (SELECT format('SELECT * FROM %I.%I', t.schemaname, t.tablename)) q
                        CROSS JOIN LATERAL connection_to_regclass(q) AS r
                    ) subq
                )
            ) as copy_data
        FROM pg_tables t
        WHERE t.schemaname = 'public'
    )
    SELECT string_agg(copy_data, E'\n')
    FROM table_data;
    