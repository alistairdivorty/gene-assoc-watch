from jobs.gda import extract_, transform_


class TestGda:
    def test_gene_disease_associations_extracted(self, spark):
        df = extract_(spark)
        df = transform_(df)

        df.show()

        assert df.count() is not None
