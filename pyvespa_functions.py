from vespa.package import ApplicationPackage, Field, Schema, Document, RankProfile, HNSW, RankProfile, Component, Parameter, FieldSet, GlobalPhaseRanking, Function, Summary

tfidf_rank_profile = RankProfile(
        name="tfidf_rank",
        first_phase="nativeRank(title) + nativeRank(body)"
    )

bm25_rank_profile = RankProfile(
                        name="bm25", 
                        first_phase="bm25(title) + bm25(body)"
                    )

semantic_search_rank_profile = RankProfile(
                        name="semantic", 
                        inputs=[("query(q)", "tensor<float>(x[384])")],
                        first_phase="closeness(field, embedding)"
                    )
fusion_rank_profile = RankProfile(
                        name="fusion", 
                        inherits="bm25",
                        inputs=[("query(q)", "tensor<float>(x[384])")],
                        first_phase="closeness(field, embedding)",
                        global_phase=GlobalPhaseRanking(
                            expression="reciprocal_rank_fusion(bm25sum, closeness(field, embedding))",
                            rerank_count=1000
                        )
                    )   


def create_package(app_type="semantic-search"):
    if app_type == "semantic-search":
        package = ApplicationPackage(
            name="findmypasta",
            schema=[Schema(
                name="doc",
                document=Document(
                    fields=[
                        Field(name="id", type="string", indexing=["summary"]),
                        Field(name="title", type="string", indexing=["index", "summary"], index="enable-bm25"),
                        Field(name="body", type="string", indexing=["index", "summary"], index="enable-bm25", bolding=True),
                        Field(name="embedding", type="tensor<float>(x[384])",
                            indexing=["input title . \" \" . input body", "embed", "index", "attribute"],
                            ann=HNSW(distance_metric="angular"),
                            is_document_field=False
                        )
                    ]
                ),
                fieldsets=[
                    FieldSet(name="default", fields=["title", "body"])
                ],
                rank_profiles=[
                    bm25_rank_profile,
                    semantic_search_rank_profile,
                    fusion_rank_profile             
                ]
            )
            ],
            components=[Component(id="e5", type="hugging-face-embedder",
                parameters=[
                    Parameter("transformer-model", {"url": "https://github.com/vespa-engine/sample-apps/raw/master/simple-semantic-search/model/e5-small-v2-int8.onnx"}),
                    Parameter("tokenizer-model", {"url": "https://raw.githubusercontent.com/vespa-engine/sample-apps/master/simple-semantic-search/model/tokenizer.json"})
                ]
            )]
        ) 
    elif app_type == "text-search":
        package = ApplicationPackage(
            name="findmypasta",
            schema=[
                Schema(
                    name="doc",
                    document=Document(
                        fields=[
                            Field(name="id", type="string", indexing=["summary"]),
                            Field(name="title", type="string", indexing=["index", "summary"], index="enable-bm25"),
                            Field(name="body", type="string", indexing=["index", "summary"], index="enable-bm25", bolding=True)
                        ]
                    ),
                    fieldsets=[
                        FieldSet(name="default", fields=["title", "body"])
                    ],
                    rank_profiles=[
                        bm25_rank_profile,
                        tfidf_rank_profile
                    ]
                )
            ]
        )

        
    return package

# get model endpoint - get_model_endpoint

from vespa.io import VespaResponse
from ipywidgets import IntProgress, VBox, Label, Layout  # Import Layout for styling
from IPython.display import display
import time

class VespaFeeder:
    def __init__(self, app):
        self.app = app

    def feed(self, data_to_feed):
        self.vespa_feed_slice = data_to_feed.apply(self.to_vespa_format, axis=1)

        # Create a progress bar widget
        self.progress_bar = IntProgress(min=0, max=len(self.vespa_feed_slice), description='Progress:', layout=Layout(width='50%'))
        self.progress_label = Label(value="Feeding documents: 0/{}".format(len(self.vespa_feed_slice)))

        display(VBox([self.progress_bar, self.progress_label]))
        self.start_time = time.time()

        self.app.feed_iterable(self.vespa_feed_slice, schema="doc", namespace="findmypasta", callback=self.callback)

    def to_vespa_format(self, x):
        return {"id": x["id"], "fields": { "title": x["title"], "body": x["body"], "id": x["id"]}}


    def callback(self, response: VespaResponse, id: str):
        if not response.is_successful():
            print(f"Error when feeding document {id}: {response.get_json()}")
        
        # Update the progress bar value
        self.progress_bar.value += 1
        self.progress_label.value = f"Feeding documents: {self.progress_bar.value}/{self.progress_bar.max} ({self.progress_bar.value * 100 / self.progress_bar.max:.2f}%)"
        self.update_estimated_time()

    def update_estimated_time(self):
        if self.progress_bar.value > 0:
            self.progress_bar.bar_style = 'info'
            self.progress_bar.style.bar_color = '#00AA00'
            self.progress_bar.style.description_width = 'initial'
            remaining_documents = self.progress_bar.max - self.progress_bar.value
            time_per_document = (time.time() - self.start_time) / self.progress_bar.value
            estimated_remaining_time = remaining_documents * time_per_document
            self.progress_bar.description = f'Progress: (ETA: {self.format_time(estimated_remaining_time)})'

    def format_time(self, time_in_seconds: float) -> str:
        hours = int(time_in_seconds // 3600)
        time_in_seconds = time_in_seconds - (hours * 3600)
        minutes = int(time_in_seconds // 60)
        seconds = int(time_in_seconds - (minutes * 60))
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"