from signposting import LinkRel, Signpost


def create_signposting_link(rel: LinkRel, target: str) -> str:
    """
    Create a signposting link
    Args:
        rel: Link relation (enum signposting.signpost.LinkRel)
        target: URI

    Returns:
        signposting link string for signpostinglinks concatenation
    """
    signposting_link = str(Signpost(rel=LinkRel.type, target=target))
    if signposting_link.startswith("Link: "):
        return signposting_link[6:]
    else:
        raise Exception("Unexpected signposting link format", target, rel)




def datacite_to_signposting_links(datacite_dict):
    """"""
    datacite_links = []
    # author
    for attribute in datacite_dict.get("data").get("attributes").get("creators"):
        for name_identifier in attribute["nameIdentifiers"]:
            datacite_links.append(create_signposting_link(rel=LinkRel.author, target=name_identifier["nameIdentifier"]))
    # license
    for attribute in datacite_dict.get("data").get("attributes").get("rightsList"):
        datacite_links.append(create_signposting_link(rel=LinkRel.license, target=attribute["rightsUri"]))
    # type
    # for attribute in datacite_dict.get("data").get("attributes").get("rightsList"):
    #     datacite_links.append(create_signposting_link(rel=LinkRel.license, target=attribute["rightsUri"]))

    # cite-as



    links_dict = {
        "Link": ", ".join(datacite_links)
    }
    return links_dict