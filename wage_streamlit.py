import pandas as pd
import streamlit as st
import pydeck as pdk  # 三次元グラフ用ライブラリ
import plotly.express as px  # グラフなどビジュアル化ツール

# ダッシュボードのタイトルを設定
st.title('「日本の賃金データ」ダッシュボード')

# jp／indデータ読み込み
df_jp_ind = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_全国_全産業.csv', encoding='shift_jis')
# jp／categoryデータ読み込み
df_jp_category = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_全国_大分類.csv', encoding='shift_jis')
# pref／indデータ読み込み
df_pref_ind = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_都道府県_全産業.csv', encoding='shift_jis')
# pref／categoryデータは不要
# df_pref_category = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_都道府県_大分類.csv', encoding='shift_jis')

st.header('■2019年：一人当たり賃金のヒートマップ')

# 各県庁所在地の緯度経度を記したCSVファイル（講師提供）を読み込む
jp_lat_lon = pd.read_csv('./pref_lat_lon.csv')

# この緯度経度CSVの都道府県名の列名は「pref_name」となっているが、
# これをデータファイル同様に「都道府県名」に変更する。
# CSV自体を変更するのではなく読込後のDataFrameの列名を変更する
jp_lat_lon = jp_lat_lon.rename(columns={'pref_name': '都道府県名'})

# 「都道府県別・全産業／pref・ind」データを対象に、
# 年齢が「年齢計」、集計年が「2019年」のデータのみを集めた
# DataFrame〔df_pref_map〕を新たに作成する
df_pref_map = df_pref_ind[(df_pref_ind['年齢'] == '年齢計') & (df_pref_ind['集計年'] == 2019)]

# 〔jp_lat_lon〕は「都道府県名」×「緯度・経度（マップ）」
# 〔df_pref_map〕は「都道府県名」×「2019年の一人当たり賃金」
# と捉えれば、両者を結合させることで、「緯度経度」×「一人当たり賃金」が取得でき
# マップ上に賃金（の違い）を表現できる。結合には〔merge〕メソッドを用いる
# ３つ目の引数〔on〕は、省略すれば名前が一致する列名がキーとして用いられる。
# 今回は明示的に指定している
df_pref_map = pd.merge(df_pref_map, jp_lat_lon, on='都道府県名')

# 賃金データを生データではなく、最小値0、最大値1となる形で正規化して用いる。
# 変換式：Y＝（X－Xmin）／（Xmax－Xmin）
# 変換後の値（項目）を「一人当たり賃金（相対値）」とする。
# 長い計算式（コード）なので、バックスラッシュ〔\〕で区切った。
df_pref_map['一人当たり賃金（相対値）']=\
    (df_pref_map['一人当たり賃金（万円）']-df_pref_map['一人当たり賃金（万円）'].min())\
    /(df_pref_map['一人当たり賃金（万円）'].max()-df_pref_map['一人当たり賃金（万円）'].min())
# df_pref_map  # マジックコマンド

# (1)view設定：つまり見た目をどうするか
view = pdk.ViewState(
    # どこを中心にしてみたいのか（初期値）
    longitude = 139.691648,  # その経度
    latitude = 35.689185,  # その緯度
    zoom = 4,  # 表示サイズ
    pitch = 40.5  # 視点角度
)

# (2)layer設定：グラフ化するためのデータ指定など
layer = pdk.Layer(
    'HeatmapLayer',  # pydeckに用意されている〔HeatmapLayer〕を使用
    data = df_pref_map,  # 正規化データを追加したDataFrame
    opacity = 0.4,  # 不透明度設定
    get_position = ['lon', 'lat'],  # pydeckでは経度・緯度の順番
    threshold = 0.3,  # ヒートマップ描画時の「しきい値」
    get_weight = '一人当たり賃金（相対値）'  # どの列をマップ化するか（複数列ある場合）
)

# (3)レンダリング
layer_map = pdk.Deck(
    # 今まで定義してきたviewとlayerを引数にDeckメソッドを適用
    layers = layer,
    # layers = hexagon_layer,
    initial_view_state = view,
)

# (4)レンダリング結果の表示
st.pydeck_chart(layer_map)

# チェックボックスにチェックを入れたら表も確認できるようにしておく
show_df = st.checkbox('Show DataFrame')
if show_df == True:
    st.write(df_pref_map)

# ここからは賃金の時系列推移-------------------------------

st.header('■集計年別の一人当たり賃金の推移')

# (1)全国の平均賃金推移には、〔全国・全産業／jp・ind〕のDataFrameを使う
# 「年齢計」の行だけ抽出して新しいDataFrameを作る
df_ts_mean = df_jp_ind[(df_jp_ind['年齢'] == '年齢計')] 
# df_ts_meanの〔ts〕って何？

# 以下（丸括弧なし）でもエラーにならない（ちゃんとデータも取得できている）
# df_ts_mean = df_jp_ind[df_jp_ind['年齢'] == '年齢計']

# 全国のデータであることがわかるように列名を変更しておく。
df_ts_mean = df_ts_mean.rename(columns={'一人当たり賃金（万円）':'全国平均賃金'})

# (2)都道府県毎の平均賃金では、「都道府県・全産業／pref・ind」のDataFrameを使う
# こちらも「年齢計」の行を抜き出して新しいDataFrameにする
df_pref_mean = df_pref_ind[(df_pref_ind['年齢'] == '年齢計')]

# 都道府県のデータも列名を変更しておく。
df_pref_mean = df_pref_mean.rename(columns={'一人当たり賃金（万円）':'平均賃金'})

# 都道府県名を重複なしに取り出す
pref_list = df_pref_mean['都道府県名'].unique()

# 取り出した都道府県名リストをセレクトボックスに候補として表示する
option_pref = st.selectbox(  # 選択された都道府県名が入る変数
    '都道府県',  # 上に表示する文字（「性別を選んで下さい」みたいな）
    (pref_list)  # このようにすれば都道府県が一覧表示されるようだ
)

df_pref_mean = df_pref_mean[df_pref_mean['都道府県名'] == option_pref]
# これにより〔df_pref_mean〕が、選んだ都道府県データのみで上書きされるが、
# 次に異なる県を選択してもちゃんと新しい県のデータが取得・表示できるのか。

# 以前は片方にもう片方を吸収させたが、ここでは
# df_ts_mean／df_pref_meanを結合して新たに〔df_mean_lines〕を作成
df_mean_line = pd.merge(df_ts_mean, df_pref_mean, on='集計年')

# グラフ化に必要な列「集計年」「全国平均賃金」「平均賃金」に絞り込む
df_mean_line = df_mean_line[['集計年', '全国平均賃金', '平均賃金']]

# 上記を下行のように一重括弧にしたらエラーになった
# df_mean_line = df_mean_line['集計年', '全国平均賃金', '平均賃金']

# 集計年をｘ軸に使えるように、これをindex化する
df_mean_line = df_mean_line.set_index('集計年')

df_mean_line

# 折れ線グラフ〔line_chart〕を描く
st.line_chart(df_mean_line)

# 年齢階級別賃金のバブルチャートとアニメーション----------------------------

# 新しいヘッダーとして「■年齢階級別の全国平均賃金」とする。
st.header('■年齢階級別の全国平均賃金')

# 「全国・全産業／jp・ind」のデータを用いて新たなDataFrame作成
# 今回は「年齢計」のみを除外してその他全ての年齢階級を用いる
df_mean_bubble = df_jp_ind[df_jp_ind['年齢'] != '年齢計']

# ｘ軸に一人当たり賃金、ｙ軸に年間賞与、バブルサイズに所定内給与を充てる
# 本来、所定内給与と年間賞与から年収（一人当たり賃金）が決まるので、
# 結果変数である年収（一人当たり賃金）をバブルサイズにすべき
# この話はあくまでもこの３変数に限った場合で、本来は年齢階級を横軸にすべき

# Plotly Expressで散布図やバブルチャートを描く際には〔scatter〕メソッドを用いる
fig = px.scatter(df_mean_bubble,
    x = '一人当たり賃金（万円）',
    y = '年間賞与その他特別給与額（万円）',
    range_x = [150, 700],  # x軸目盛りの上下限
    range_y = [0, 150],  # y軸目盛りの上下限
    size = '所定内給与額（万円）',  # バブルサイズに充てる変数
    size_max = 38,  # バブルの大きさの最大値
    color = '年齢',  # 年齢階級に応じて色を変える
    animation_frame = '集計年',  # 時間経過に応じて「集計年」が進む
    animation_group = '年齢'  # 今ひとつ意味が分からない
)
st.plotly_chart(fig)

# 産業別の賃金を横棒で表現する。------------------------------------------

st.header('■産業別の賃金推移')

# まず集計年の一覧（ダブりなし）を取得する。
year_list = df_jp_category['集計年'].unique()

# セレクトボックスでユーザーに年を選択してもらう。
option_year = st.selectbox(
    '集計年を選んでね',
    (year_list))

# 表示する賃金項目もユーザーにセレクトボックスで選択してもらう。
wage_list = ['所定内給与額（万円）', '年間賞与その他特別給与額（万円）', '一人当たり賃金（万円）']
option_wage = st.selectbox(
    '表示する賃金項目を選んでね',
    (wage_list))

# 今回は「全国・産業別／jp・category」データを利用する。
# その中から、上で選択された集計年のデータを抽出する。
# なんで〔category〕ではなく〔categ〕なんだ？　一貫性がない！
df_mean_categ = df_jp_category[(df_jp_category['集計年'] == option_year)]

# ユーザーがどの賃金項目を選択するかによって、グラフの目盛りを変える必要があるので、
# 賃金項目ごとにデータの最大値を取得してそれに少し余裕を持たせて目盛り上限を決める
max_x = df_mean_categ[option_wage].max() + 20
# max_x = df_mean_categ[option_wage].max()

# Plotly Expressで棒線グラフを描くには〔bar〕メソッドを用いる
fig2 = px.bar(df_mean_categ,
    x = option_wage,  # 選ばれた賃金項目（横方向なのでこうなる）
    y = '産業大分類名',  # 縦方向
    color = '産業大分類名',  # 産業によって色を変える
    animation_frame = '年齢',  # 時間経過によって年齢階級を変化させる
    range_x = [0, max_x],  # 横方向の目盛り上下限
    orientation = 'h',  # 「h」にすると横棒グラフになるらしい
    width = 800,
    height = 500)

st.plotly_chart(fig2)

# 末尾に記載すべき出典に関する事項
st.text('出典：RESAS（地域経済分析システム）')
st.text('本結果はRESAS（地域経済分析システム）を加工して作成')
