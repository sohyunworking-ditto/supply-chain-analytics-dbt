{#
  폴더별 +schema 값을 접두어 없이 그대로 씁니다 (staging, intermediate, marts ...).
  dev와 ci는 DuckDB 파일 자체가 분리되어 있어서 스키마에 타깃 이름을 붙일 필요가 없습니다.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
