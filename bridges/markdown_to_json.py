import re


def markdown_to_json(md):
    return snippet_to_json(md)

def snippet_to_json(md):
    """
    recursively convert markdown to json
    """
    data = {}
    
    # is first line a header?
    if md.startswith("#"):
        level = md.find("# ") + 1

        # search for the next header of same level with a space or a \n after the last #
        next_level = re.match("(?<=\n)#{" + str(level) + "}(?=(\n|\s))", md)

        # if there is no next level, we are at the end of the file
        if next_level == -1:
            next_level = len(md)

        # get key and value
        line_end = md.find("\n")
        key = md[level + 1:line_end]

        # add to data
        data[key] = {}

        # get next sub level
        next_sub_level = re.match("(?<=\n)#{" + str(level + 1) + "}(?=(\n|\s))", md[line_end+1:next_level])
        if next_sub_level != -1:

            data[key]["root"] = md[line_end+1:next_sub_level]

            current_sub_level = next_sub_level
            while current_sub_level != None:
                next_sub_level = re.match("(?<=\n)#{" + str(level + 1) + "}(?=(\n|\s))", md[current_sub_level+1:next_level])
                if next_sub_level != None:
                    data[key].update(snippet_to_json(md[current_sub_level+1:next_sub_level]))
                else:
                    data[key].update(snippet_to_json(md[current_sub_level+1:next_level]))
                current_sub_level = next_sub_level

    return data


md = open("content.md", "r").read()

print(markdown_to_json(md))


"""
def snippet_to_json(md):
    data = {}
    if md.startswith("#"):
        print("Searching in", md)
        level = md.find("# ") + 1
        line_end = md.find("\n")
        key = md[level + 1:line_end]

        data[key] = {}

        next_level = "#" * (level + 1)
        next_level = "\n" + next_level + " "

        # retrieve root information
        if md.find(next_level) != -1:
            data[key]["root"] = md[line_end+1:md.find(next_level)]
        else:
            data[key]["root"] = md[line_end+1:]

        current_index = md.find(next_level) + 1
        
        while current_index != 0:
            next_index = md[current_index:].find(next_level) + 1
            data[key].update(snippet_to_json(md[current_index:next_index-1]))
            current_index = next_index
    return data


"""