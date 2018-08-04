class TestsEsUtil:
    @classmethod
    def delete_alias(cls, elastic_search, alias_name):
        if elastic_search.indices.exists_alias(alias_name):
            indices = elastic_search.indices.get_alias(alias_name)

            for index in indices:
                elastic_search.indices.delete_alias(index, alias_name)
                elastic_search.indices.delete(index)
