import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:video_player/video_player.dart';
// import 'package:video_thumbnail/video_thumbnail.dart';
import 'package:permission_handler/permission_handler.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TrueVision',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: DeepfakeDetector(),
    );
  }
}

class DeepfakeDetector extends StatefulWidget {
  const DeepfakeDetector({super.key});
  @override
  State<DeepfakeDetector> createState() => _DeepfakeDetectorState();
}

class _DeepfakeDetectorState extends State<DeepfakeDetector> {
  File? _videoFile;
  String _result = '';
  bool _isLoading = false;
  VideoPlayerController? _controller;
  String _confidenceLabel = '';
  String _resultLabel = '';
  String _hostip = "192.168.1.38";

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> requestStoragePermission() async {
    if (await Permission.storage.request().isGranted) {
      // The permission is granted, you can proceed with accessing storage
    } else {
      // The permission is denied, you can handle the denial here
      // For example, you might want to show a dialog to the user
    }
  }

  Future<void> _pickVideo() async {
    setState(() {
      _result = "";
    });
    await requestStoragePermission();
    final pickedFile =
        await ImagePicker().pickVideo(source: ImageSource.gallery);

    if (pickedFile != null) {
      setState(() {
        _videoFile = File(pickedFile.path);
        _controller = VideoPlayerController.file(_videoFile!)
          ..initialize().then((_) {
            setState(() {});
          });
      });
    }
  }

  Future<void> _uploadVideo() async {
    if (_videoFile == null) return;

    // setState(() {
    //   _isLoading = true;
    // });

    try {
      var request = http.MultipartRequest(
          'POST', Uri.parse('http://$_hostip:3000/api'));
      request.files
          .add(await http.MultipartFile.fromPath('video', _videoFile!.path));
      var res = await request.send();

      if (res.statusCode == 200) {
        var responseData = await res.stream.bytesToString();
        var result = jsonDecode(responseData);

        setState(() {
          _result =
              'Video is: ${result['output']} (Confidence: ${result['confidence']}%)';
          _isLoading = false;
          _resultLabel = result['output'];
          _confidenceLabel = result['confidence'].toString();
          debugPrint(_resultLabel);
          debugPrint(_confidenceLabel);
        });
      } else {
        throw Exception('Failed to get result. Status code: ${res.statusCode}');
      }
    } catch (e) {
      // setState(() {
      //   // _result = 'Failed to get result. Please try again.';
      //   _isLoading = false;
      // });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Scaffold(
        appBar: AppBar(
          backgroundColor: Colors.red.shade100,
          centerTitle: true,
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                'TrueVision',
                style: TextStyle(fontSize: 20, color: Colors.red.shade300),
              ),
              
            ],
          ),
        ),
        // resizeToAvoidBottomInset: false,
        body: SingleChildScrollView(
          padding: EdgeInsets.all(12),
          child: Column(
                  children: [
                    (_videoFile == null)
                        ? Center(
                            child: Column(
                              children: [
                                TextWall(),
                                SizedBox(
                                  height: 32,
                                ),
                                InkWell(
                                  onTap: _pickVideo,
                                  child: Container(
                                    decoration: BoxDecoration(
                                        border: Border.all(
                                            color: Colors.purple.shade300,
                                            width: 2),
                                        color: Colors.purple.shade100,
                                        borderRadius: BorderRadius.circular(12)),
                                    height:
                                        MediaQuery.of(context).size.height / 4.5,
                                    width:
                                        MediaQuery.of(context).size.width / 2.5,
                                    padding: EdgeInsets.all(12),
                                    child: Column(
                                      children: [
                                        Icon(
                                          Icons.video_call_outlined,
                                          size: 100,
                                          color: Colors.purple.shade300,
                                        ),
                                        Text(
                                          "Pick Video",
                                          style: TextStyle(
                                              color: Colors.purple.shade300,
                                              fontSize: 20,
                                              fontWeight: FontWeight.bold),
                                        )
                                      ],
                                    ),
                                  ),
                                ),
                                SizedBox(
                                  height: 32,
                                ),
                                TextFormField(
                                  initialValue: _hostip,
                                  decoration: InputDecoration(
                                    border: OutlineInputBorder(),
                                    focusedBorder: OutlineInputBorder(
                                      borderSide: BorderSide(
                                          color: Colors.purple.shade300,
                                      )
                                    )
                                  ),
                                  onChanged: (value) => setState(() => _hostip = value),
                                )
                              ],
                            ),
                          )
                        : _controller != null && _controller!.value.isInitialized
                            ? Center(
                                child: Column(
                                  children: [
                                    SizedBox(
                                      height:
                                          MediaQuery.sizeOf(context).height / 2,
                                      width: MediaQuery.sizeOf(context).width / 2,
                                      child: AspectRatio(
                                        aspectRatio:
                                            _controller!.value.aspectRatio,
                                        child: ClipRRect(
                                            borderRadius:
                                                BorderRadius.circular(12),
                                            child: VideoPlayer(_controller!)),
                                      ),
                                    ),
                                    SizedBox(height: 10),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        ElevatedButton(
                                          style: ButtonStyle(
                                              elevation:
                                                  WidgetStatePropertyAll(0),
                                              backgroundColor:
                                                  WidgetStatePropertyAll(
                                                      Colors.blue.shade50)),
                                          onPressed: _uploadVideo,
                                          child: Icon(
                                            Icons.search,
                                            color: Colors.blue.shade300,
                                          ),
                                        ),
                                        SizedBox(width: 4),
                                        ElevatedButton(
                                          style: ButtonStyle(
                                              elevation:
                                                  WidgetStatePropertyAll(0),
                                              backgroundColor:
                                                  WidgetStatePropertyAll(
                                                      Colors.blue.shade50)),
                                          onPressed: () {
                                            setState(() {
                                              _controller!.value.isPlaying
                                                  ? _controller!.pause()
                                                  : _controller!.play();
                                            });
                                          },
                                          child: Icon(
                                            color: Colors.blue.shade400,
                                            _controller!.value.isPlaying
                                                ? Icons.pause
                                                : Icons.play_arrow,
                                          ),
                                        ),
                                        SizedBox(width: 4),
                                        ElevatedButton(
                                            style: ButtonStyle(
                                                elevation:
                                                    WidgetStatePropertyAll(0),
                                                backgroundColor:
                                                    WidgetStatePropertyAll(
                                                        Colors.blue.shade50)),
                                            onPressed: _pickVideo,
                                            child: Icon(
                                              Icons.replay,
                                              color: Colors.blue.shade300,
                                            )),
                                      ],
                                    ),
                                    ElevatedButton(
                                        style: ButtonStyle(
                                            elevation: WidgetStatePropertyAll(0),
                                            backgroundColor:
                                                WidgetStatePropertyAll(
                                                    Colors.blue.shade50)),
                                        onPressed: (){},
                                        child: Text(
                                          "Generate Report",
                                          style: TextStyle(
                                              color: Colors.blue.shade300),
                                        )),
                                  ],
                                ),
                              )
                            : Center(child: CircularProgressIndicator()),
                    (_result.isNotEmpty)
                        ? Column(
                            children: [
                              Text(
                                _resultLabel,
                                style: TextStyle(
                                    fontSize: 60,
                                    fontWeight: FontWeight.bold,
                                    color: (_resultLabel == 'REAL')
                                        ? Colors.green.shade300
                                        : Colors.red.shade300),
                              ),
                              Text(
                                "${double.parse(_confidenceLabel).toStringAsFixed(2)}% confident",
                                style: TextStyle(
                                    fontSize: 17,
                                    fontWeight: FontWeight.bold,
                                    color: (_resultLabel == 'REAL')
                                        ? Colors.green.shade300
                                        : Colors.red.shade300),
                              ),
                            ],
                          )
                        : Container()
                  ],
                ),
        ),
      ),
    );
  }
}

class TextWall extends StatelessWidget {
  const TextWall({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        // border: Border.all(color: Colors.purple.shade300, width: 2),
        color: Colors.purple.shade100,
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(
                Icons.arrow_circle_right_rounded,
                color: Colors.purple.shade300,
                size: 50,
              ),
              SizedBox(width: 4),
              Text(
                "Choose Pick Video to feed the model.",
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: Colors.grey.shade800),
              )
            ],
          ),
          SizedBox(height: 4),
          Row(
            children: [
              Icon(
                Icons.arrow_circle_right_rounded,
                color: Colors.purple.shade300,
                size: 50,
              ),
              SizedBox(width: 4),
              Text(
                "Select glass icon under preview.",
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: Colors.grey.shade800),
              )
            ],
          ),
          SizedBox(height: 4),
          Row(
            children: [
              Icon(
                Icons.arrow_circle_right_rounded,
                color: Colors.purple.shade300,
                size: 50,
              ),
              SizedBox(width: 4),
              Text(
                "Result generated is then displayed.",
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: Colors.grey.shade800),
              )
            ],
          )
        ],
      ),
    );
  }
}

class TextWallBottomOne extends StatelessWidget {
  const TextWallBottomOne({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          Icons.arrow_circle_right_rounded,
          color: Colors.purple.shade300,
          size: 50,
        ),
        SizedBox(width: 4),
        Text(
          "Choose Pick Video and select your video.",
          style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: Colors.grey.shade800),
        )
      ],
    );
  }
}

class TextWallTop extends StatelessWidget {
  const TextWallTop({super.key});

  @override
  Widget build(BuildContext context) {
    return Text(
      """TrueVision is a state of the art deepfake detection model designed by Sinister 6. It accurately detects if a video provided by the user if fake or real. 
      Go ahead and try it yourself!
      """,
      textAlign: TextAlign.justify,
      style: TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 18,
          color: Colors.grey.shade800),
    );
  }
}