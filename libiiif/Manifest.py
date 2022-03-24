class Manifest:
    def createCanvasFromYolo(self, url, width, height, result, yolo_input_image_size, canvasIndex, isIIIF=False, thres=-1):
        if isIIIF:
            spl = url.split("/")
            prefix = url.replace("/{}/{}/{}/{}".format(spl[-4], spl[-3], spl[-2], spl[-1]), "")
        else:
            prefix = url

        r = max(width, height) / yolo_input_image_size

        items = []

        canvas = "{}/canvas".format(prefix) # /pk1

        for i in range(len(result)):
            obj = result[i]

            score = obj["confidence"]

            if thres > 0 and score < thres:
                continue

            index = i + 1
            
            x = int(obj["xmin"] * r)
            y = int(obj["ymin"] * r)
            w = int(obj["xmax"] * r) - x
            h = int(obj["ymax"] * r) - y

            xywh = "{},{},{},{}".format(x, y, w, h)

            items.append({
                "id": "{}/annos/{}".format(canvas, index),
                "motivation": "commenting",
                "target": "{}#xywh={}".format(canvas, xywh),
                "type": "Annotation",
                "body": {
                    "type": "TextualBody",
                    "value": "label:{} score:{}".format(obj["name"], round(score, 2))
                }
            })

        body = {
            "format": "image/jpeg",
            "height": height,
            
            "type": "Image",
            "width": width
        }

        if isIIIF:
            body["id"] = prefix + "/full/full/0/default.jpg"
            body["service"] = [
                {
                    "id": prefix,
                    "type": "ImageService2",
                    "profile": "level2"
                }
            ]
        else:
            body["id"] = url

        return {
            "annotations" : [
                {
                    "id" : "{}/annos".format(canvas),
                    "items" : items,
                    "type": "AnnotationPage"
                }
            ],
            "height": height,
            "id": "{}".format(canvas),
            "items": [
                {
                    "id": "{}/page".format(canvas),
                    "items": [
                        {
                            "body": body,
                            "id": "{}/page/imageanno".format(canvas),
                            "motivation": "painting",
                            "target": "{}".format(canvas),
                            "type": "Annotation"
                        }
                    ],
                    "type": "AnnotationPage"
                }
            ],
            "label" : "[{}]".format(canvasIndex),
            "type": "Canvas",
            "width": width
        }

    def createManifest(self, manifestUri, label, canvases):

        return {

            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": manifestUri,
            "type": "Manifest",
            "label": {
                "none": [
                    label
                ]
            },
            "items": canvases
        }