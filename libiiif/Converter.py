import requests
import json
from tqdm import tqdm

"""
モジュール `Converter` は，IIIFに関する変換処理を行います．
"""

class Converter:
    test = ""

    @staticmethod
    def convertCuration2Manifest3(curation):

        """
        キュレーションリストをマニフェストに変換します。
        """

        selections = curation["selections"]
        
        map = {}
        manifests = []
        for selection in selections:
            manifest = selection["within"]["@id"]
            if manifest not in manifests:
                manifests.append(manifest)
            
            members = selection["members"]

            for member in members:
                member_id = member["@id"]
                spl = member_id.split("#xywh=")
                canvas_id = spl[0]
                xywh= spl[1]

                if canvas_id not in map:
                    map[canvas_id] = []

                chars = member["metadata"][0]["value"][0]["resource"]["chars"]
                
                map[canvas_id].append({
                    "xywh": xywh,
                    "label": chars
                })

        canvases3 = []

        for manifest in tqdm(manifests):
            manifestData = requests.get(manifest).json()
            canvases = manifestData["sequences"][0]["canvases"]

            for i in tqdm(range(len(canvases))):
                canvas = canvases[i]
                canvas_id = canvas["@id"]
                items = []
                if canvas_id in map:

                    values = map[canvas_id]

                    for value in values:

                        index = len(items)

                        xywh = value["xywh"]
                        label = value["label"]

                        items.append({
                            "id": "{}/annos/{}".format(canvas_id, index),
                            "motivation": "commenting",
                            "target": "{}#xywh={}".format(canvas_id, xywh),
                            "type": "Annotation",
                            "body": {
                                "type": "TextualBody",
                                "value": label
                            }
                        })

                canvasIndex = i + 1
                width = canvas["width"]
                height = canvas["height"]

                body = {
                    "format": "image/jpeg",
                    "height": height,
                    
                    "type": "Image",
                    "width": width
                }

                body["id"] = canvas["images"][0]["resource"]["@id"]
                body["service"] = [
                    {
                        "id": canvas["images"][0]["resource"]["service"]["@id"],
                        "type": "ImageService2",
                        "profile": "level2"
                    }
                ]

                canvases3.append({
                    "annotations" : [
                        {
                            "id" : "{}/annos".format(canvas_id),
                            "items" : items,
                            "type": "AnnotationPage"
                        }
                    ],
                    "height": height,
                    "id": "{}".format(canvas_id),
                    "items": [
                        {
                            "id": "{}/page".format(canvas_id),
                            "items": [
                                {
                                    "body": body,
                                    "id": "{}/page/imageanno".format(canvas_id),
                                    "motivation": "painting",
                                    "target": "{}".format(canvas_id),
                                    "type": "Annotation"
                                }
                            ],
                            "type": "AnnotationPage"
                        }
                    ],
                    "label" : "[{}]".format(canvasIndex),
                    "type": "Canvas",
                    "width": width
                })
        
        label = curation["label"]

        return {

            "@context": "http://iiif.io/api/presentation/3/context.json",
            # "id": manifestUri,
            "type": "Manifest",
            "label": {
                "none": [
                    label
                ]
            },
            "items": canvases3
        }

    def test2(self):
        """
        テストメソッド
        """
        print(self.test)
    