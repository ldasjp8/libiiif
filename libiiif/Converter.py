import requests
import json
from tqdm import tqdm
from bs4 import BeautifulSoup

"""
モジュール `Converter` は，IIIFに関する変換処理を行います．
"""

class Converter:

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
                    "label" : {
                        "none": [
                            "[{}]".format(canvasIndex)
                        ]
                    },
                    "type": "Canvas",
                    "width": width,
                    "thumbnail": [
                        {
                            "id": canvas["thumbnail"]["@id"],
                            "type": "Image",
                            "format": "image/jpeg"
                        }
                    ]
                })
        
        # label = curation["label"]
        label = manifestData["label"]
        rights = manifestData["license"]
        viewingDirection = manifestData["viewingDirection"]
        attribution = manifestData["attribution"]
        attribution = "『{}』({}所蔵)を改変".format(manifestData["label"], attribution)
        seeAlso = manifestData["seeAlso"]

        metadata2 = []
        for m in manifestData["metadata"]:
            metadata2.append({
                "label": {
                    "none": [
                        m["label"]
                    ]
                },
                "value": {
                    "none": [
                        m["value"]
                    ]
                }
            })

        metadata2.append({
            "label": {
                "none": [
                    "rights"
                ]
            },
            "value": {
                "none": [
                    rights
                ]
            }
        })

        id = seeAlso.split("/")[-1]

        result = {

            "@context": "http://iiif.io/api/presentation/3/context.json",
            # "id": "https://d1fasenpql7fi9.cloudfront.net/v1/manifest/{}.json".format(id),
            "type": "Manifest",
            "label": {
                "none": [
                    label
                ]
            },
            "metadata": metadata2,
            "requiredStatement": {
                "label":  {
                    "none": [
                        "Attribution"
                    ]
                },
                "value": {
                    "none": [
                        attribution
                    ]
                }
            },
            # "rights": rights,
            "viewingDirection": viewingDirection,
            "seeAlso": [
                {
                    "id": seeAlso,
                    "type": "Dataset",
                    "label": {
                        "none": [
                            "OAI-PMH"
                        ]
                    },
                    "format": "application/xml"
                }
            ],
            "homepage": [
                {
                    "id": "https://dl.ndl.go.jp/info:ndljp/pid/{}".format(id),
                    "type": "Text",
                    "label": {
                        "none": [
                            label
                        ]
                    },
                    "format": "text/html",
                    "language": [
                        "ja"
                    ]
                }
            ],
            "items": canvases3
        }

        if "structures" in manifestData:
            structures = manifestData["structures"]
            structures2 = []
            for structure in structures:
                items = []
                structure2 = {
                    "id": structure["@id"],
                    "type": structure["@type"].replace("sc:", ""),
                    "label": {
                        "none": [
                            structure["label"]
                        ]
                    },
                    "items": items
                }
                structures2.append(structure2)
                
                for canvas_id in structure["canvases"]:
                    items.append({
                        "id": canvas_id,
                        "type": "Canvas"
                    })
                # structure["items"] = items
                # del structure["canvases"]
            result["structures"] = structures2

        return result

    @staticmethod
    def convertManifest3ToTEI(manifest):

        """
        IIIFマニフェスト3をTEIに変換します。
        """
        
        htmlText = '''
        <?xml-model href="https://raw.githubusercontent.com/ldasjp8/tei-example/main/tei_all.rng" schematypens="http://relaxng.org/ns/structure/1.0" type="application/xml"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>{}</title>
                    </titleStmt>
                    <publicationStmt>
                        <p>{}</p>
                    </publicationStmt>
                    <sourceDesc>
                        <p>{}</p>
                    </sourceDesc>
                </fileDesc>
            </teiHeader>
            <text>
                <body>
                </body>
            </text>
            <facsimile></facsimile>
        </TEI>
        '''.format(manifest["label"]["none"][0], "Satoru Nakamura", "国立国会図書館 National Diet Library, JAPAN")

        bs = BeautifulSoup(htmlText, "xml")

        facsimile = bs.find("facsimile")
        facsimile["source"] = manifest["id"]
            
        items = manifest["items"]

        count = 0

        for i in range(len(items)):
            item = items[i]
            canvas_id = item["id"]
            annotations = item["annotations"][0]["items"]
            
            pb = bs.new_tag('pb')
            index = i + 1
            zindex = str(index).zfill(4)
            
            div = bs.new_tag('div')
            div["n"] = index
            bs.find("body").append(div)
            
            pb["n"] = index
            pb["corresp"] = "#page{}".format( zindex)
            div.append(pb)
            
            # surface
            surface = bs.new_tag('surface')
            surface["source"] = canvas_id
            surface["n"] = index
            facsimile.append(surface)
            
            for annotation in annotations:
                member_id = annotation["target"]
                chars = annotation["body"]["value"]
            
                spl = member_id.split("#xywh=")
                xywh = spl[1]

                # ab
                ab = bs.new_tag('ab')
                ab.string = chars
                
                # zone_id = "zone_{}_{}".format(zindex, xywh)
                zone_id = "z{}".format(count)

                count += 1
                
                ab["facs"] = "#" + zone_id
                
                div.append(ab)
                
                # zone
                zone = bs.new_tag('zone')
                surface.append(zone)
                zone["xml:id"] = zone_id
                
                spl = xywh.split(",")
                
                x = int(spl[0])
                y = int(spl[1])
                w = int(spl[2])
                h = int(spl[3])
                
                zone["ulx"] = x
                zone["uly"] = y
                zone["lrx"] = x + w
                zone["lry"] = y + h

        return str(bs) # .prettify()

    def test2(self):
        """
        テストメソッド
        """
        print(self.test)
    