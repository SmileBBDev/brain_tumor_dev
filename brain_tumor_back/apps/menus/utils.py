def build_menu_tree(menus):
    menu_map = {}
    tree = []

    for menu in menus:
        labels = {lbl.role: lbl.text for lbl in menu.labels.all()}
        menu_map[menu.id] = {
            "id": menu.id,
            "path": menu.path,
            "icon": menu.icon,
            "groupLabel": menu.group_label,
            "breadcrumbOnly": menu.breadcrumb_only,
            "labels": labels,
            "children": [],
        }

    for menu in menus:
        if menu.parent_id:
            if menu.parent_id in menu_map:
                menu_map[menu.parent_id]["children"].append(menu_map[menu.id])
        else:
            tree.append(menu_map[menu.id])

    return tree