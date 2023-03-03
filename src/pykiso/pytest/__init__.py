# session.config.hook.pytest_collectstart(collector=module_collector)
# module_report = session.config.hook.pytest_make_collect_report(collector=module_collector)
# session.config.hook.pytest_collectreport(report=module_report)

# for collected_test_case in module_collector.collect():
#     session.config.hook.pytest_collectstart(collector=collected_test_case)
#     class_report = session.config.hook.pytest_make_collect_report(collector=collected_test_case)
#     session.config.hook.pytest_collectreport(report=class_report)

#     for collected_test_method in collected_test_case.collect():
#         session.config.hook.pytest_collectstart(collector=collected_test_method)
#         session.config.hook.pytest_itemcollected(item=collected_test_method)
#         collected_test_items.append(collected_test_method)


# collected_test_suites.append(
#     sorted(
#         collected_test_items,
#         key=lambda tc: tc_sort_key(tc.parent._obj(tc.name))
#     )
# )
