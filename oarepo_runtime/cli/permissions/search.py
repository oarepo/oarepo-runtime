import json
import sys

import click
import yaml
from invenio_records_resources.proxies import current_service_registry

from oarepo_runtime.info.permissions.debug import add_debugging, merge_communities

from .base import get_user_and_identity, permissions


@permissions.command(name="search")
@click.argument("user_id_or_email")
@click.argument("service_name")
@click.option("--explain/--no-explain", default=False)
@click.option("--user/--published", "user_call", default=False)
@click.option("--full-query/--query-filters", default=False)
@click.option("--merge-communities", "do_merge_communities", is_flag=True)
@click.option("--json/--yaml", "as_json", default=False)
def search_permissions(
    user_id_or_email,
    service_name,
    explain,
    user_call,
    full_query,
    do_merge_communities,
    as_json,
):
    """Get search parameters for a given service."""
    try:
        service = current_service_registry.get(service_name)
    except KeyError:
        raise click.UsageError(
            f"Service {service_name} not found in {current_service_registry._services.keys()}"
        )
    user, identity = get_user_and_identity(user_id_or_email)

    permission_policy = service.config.permission_policy_cls

    add_debugging(print_search=explain, print_needs=False, print_excludes=False)

    if full_query:
        previous_search = service._search

        class NoExecute:
            def __init__(self, query):
                self.query = query

            def execute(self):
                return self.query

        def _patched_search(*args, **kwargs):
            ret = previous_search(*args, **kwargs)
            return NoExecute(ret)

        def _patched_result_list(self, identity, results, params, **kwargs):
            return results

        service._search = _patched_search
        service.result_list = _patched_result_list

        if user_call:
            ret = service.search_drafts(identity)
        else:
            ret = service.search(identity)
        ret = ret.to_dict()
        if do_merge_communities:
            ret = merge_communities(ret)
        ret = {
            "query": ret["query"],
        }
        dump_dict(ret, as_json)
    else:

        over = {}
        if explain:
            over["debug_identity"] = identity
            print("## Explaining search:")

        if user_call:
            p = permission_policy("read_draft", identity=identity, **over)
        else:
            p = permission_policy("read_deleted", identity=identity, **over)
        query_filters = p.query_filters

        print()
        print("## Query filters:")
        for qf in query_filters:
            dict_qf = qf.to_dict()
            if explain:
                dict_qf = merge_communities(dict_qf)
            dump_dict(dict_qf, as_json)
            print(json.dumps(dict_qf, indent=2))


def merge_name(d):
    if isinstance(d, list):
        return [merge_name(x) for x in d]
    if isinstance(d, dict):
        ret = {}
        for k, v in d.items():
            v = merge_name(v)
            if isinstance(v, dict) and "_name" in v:
                _name = v.pop("_name")
                _name = _name.split("@")[0].strip()
                k = f"{k}[{_name}]"
            ret[k] = v
        return ret
    return d


def dump_dict(d, as_json=False):
    if as_json:
        print(json.dumps(d, indent=2))
    else:
        yaml.safe_dump(
            merge_name(json.loads(json.dumps(d))),
            sys.stdout,
            default_flow_style=False,
        )
